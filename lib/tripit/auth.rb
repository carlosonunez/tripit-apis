require 'aws-sdk-dynamodb'
require 'tripit/aws_helpers/api_gateway'
require 'tripit/core'
require 'logger'
require 'securerandom'
require 'dynamoid'

module TripIt
  module Auth
    class TripItToken
      Dynamoid.configure do |config|
        config.namespace = "tripit_auth_state_#{ENV['ENVIRONMENT'].downcase}"
        config.logger.level = Logger::FATAL
      end

      include Dynamoid::Document
      table name: :tokens, key: :access_key, read_capacity: 2, write_capacity: 2
      field :access_key
      field :tripit_token
      field :tripit_token_secret
    end

    class TripItAuthState
      Dynamoid.configure do |config|
        config.namespace = "tripit_auth_state_#{ENV['ENVIRONMENT'].downcase}"
        config.logger.level = Logger::FATAL
      end

      include Dynamoid::Document
      table name: :state_associations, key: :tripit_token, read_capacity: 2, write_capacity: 2
      field :access_key
      field :tripit_token
      field :tripit_token_secret
    end

    def self.begin_authentication_flow(event)
      if !self.configure_aws!
        return TripIt::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      if !self.reauthenticate?(event: event) and self.has_token? event: event
        return TripIt::AWSHelpers::APIGateway.ok(message: 'You already have a token.')
      end
      begin
        token_data = TripIt::Core::OAuth::Request.get_tokens
        token = token_data[:token]
        token_secret = token_data[:token_secret]
      rescue Exception => e
        return TripIt::AWSHelpers::APIGateway.error(message: "Failed to get a TripIt token: #{e}")
      end
      redirect_uri = "https://#{TripIt::AWSHelpers::APIGateway.get_endpoint(event)}/callback"
      tripit_authorization_uri = [
        "https://www.tripit.com/oauth/authorize?oauth_token=#{token}",
        "oauth_callback=#{redirect_uri}"
      ].join '&'
      message = "You will need to authenticate into TripIt first; click on or \
copy/paste this URL to get started: #{tripit_authorization_uri}"
      if !self.associate_access_key_to_state_id!(event: event,
          token: token,
          token_secret: token_secret)
        return TripIt::AWSHelpers::APIGateway.error(
          message: "Couldn't map state to access key.")
      end
      return TripIt::AWSHelpers::APIGateway.ok(message: message)
    end

    def self.handle_callback(event)
      if !self.configure_aws!
        return TripIt::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      parameters = event['queryStringParameters']
      token_changed = false
      original_token = parameters['oauth_token']
      if original_token.nil?
        return TripIt::AWSHelpers::APIGateway.error(
          message: "TripIt didn't send a oauth_token upon calling back.")
      else
        original_token_secret = self.get_token_secret_from_state(token: original_token)
      begin
        token_data = TripIt::Core::OAuth::Access.get_tokens(
          request_token: original_token,
          request_token_secret: original_token_secret)
        token = token_data[:token]
        token_secret = token_data[:token_secret]
      rescue Exception => e
        return TripIt::AWSHelpers::APIGateway.error(
          message: "Failed to get a TripIt access token: #{e}")
      end
        access_key_from_state = self.get_access_key_from_state(token: original_token)
        if access_key_from_state.nil?
          return TripIt::AWSHelpers::APIGateway.error(
            message: "No access key exists for this TripIt token: #{token}")
        end
        if self.has_token?(event: event, access_key: access_key_from_state)
          token_changed = true
          self.delete_existing_tripit_tokens!(access_key: access_key_from_state)
        end
        if self.put_tripit_token(access_key: access_key_from_state,
            tripit_token: token,
            tripit_token_secret: token_secret)
          return TripIt::AWSHelpers::APIGateway.ok(additional_json: {
            token_changed: token_changed
          })
        else
          return TripIt::AWSHelpers::APIGateway.error(message: "Unable to save TripIt token.")
        end
      end
    end

    # Retrives a TripIt OAuth token from a API Gateway key
    def self.get_tripit_token(event:)
      if !self.configure_aws!
        return TripIt::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      access_key = TripIt::AWSHelpers::APIGateway::Events.get_access_key(event)
      if access_key.nil?
        return TripIt::AWSHelpers::APIGateway.error(message: 'Access key missing.')
      end
      tripit_token = self.get_tripit_token_from_access_key(access_key)
      tripit_token_secret = self.get_tripit_token_secret_from_access_key(access_key)
      if tripit_token.nil?
        return TripIt::AWSHelpers::APIGateway.not_found(
          message: 'No token exists for this access key.')
      end
      TripIt::AWSHelpers::APIGateway.ok(
        additional_json: { token: tripit_token, token_secret: tripit_token_secret })
    end

    private
    def self.get_tripit_token_from_access_key(access_key)
      begin
        results = TripItToken.where(access_key: access_key)
        return nil if results.count == 0
        results.first.tripit_token
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripIt.logger.warn("TripIt tokens table not created yet.")
        return nil
      end
    end

    def self.get_tripit_token_secret_from_access_key(access_key)
      begin
        results = TripItToken.where(access_key: access_key)
        return nil if results.count == 0
        results.first.tripit_token_secret
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripIt.logger.warn("TripIt tokens table not created yet.")
        return nil
      end
    end

    # Puts a new token and API key into DynamoDB
    def self.put_tripit_token(access_key:, tripit_token:, tripit_token_secret:)
      begin
        mapping = TripItToken.new(access_key: access_key,
                                  tripit_token: tripit_token,
                                  tripit_token_secret: tripit_token_secret)
        mapping.save
        return true
      rescue Dynamoid::Errors::ConditionalCheckFailedException
        puts "WARN: This access key already has a TripIt token. We will check for \
existing tokens and provide a refresh mechanism in a future commit."
        return true
      rescue Exception => e
        TripIt.logger.error("We weren't able to save this token: #{e}")
        return false
      end
    end

    def self.delete_existing_tripit_tokens!(access_key:)
      begin
        TripItToken.where(access_key: access_key).delete_all
      rescue => e
        puts "ERROR: Unable to delete tokens: #{e}"
      end
    end

    def self.has_token?(event:, access_key: nil)
      begin
        if access_key.nil?
          access_key = TripIt::AWSHelpers::APIGateway::Events.get_access_key(event)
        end
        results = TripItToken.where(access_key: access_key)
        return nil if results.nil? or results.count == 0
        !results.first.tripit_token.nil?
      rescue Exception => e
        TripIt.logger.warn("Error while querying for an existing token; beware stranger tings: #{e}")
        return false
      end
    end

    def self.reauthenticate?(event:)
      event.dig('queryStringParameters', 'reauthenticate') == 'true'
    end

    # Because the TripIt OAuth service invokes /callback after the
    # user successfully authenticates, /callback will not be able to resolve
    # the original client's API key. We use that API key to store their token
    # and (later) their default workspace. This fixes that by creating a
    # table mapping access keys to tokens and token secrets.
    #
    # This introduces a security vulnerability where someone can change
    # another user's TripIt token by invoking
    # /callback (a public method, as required by TripIt OAuth) with a correct
    # state ID. We will need to fix that at some point.
    def self.associate_access_key_to_state_id!(event:, token:, token_secret:)
      begin
        access_key = TripIt::AWSHelpers::APIGateway::Events.get_access_key(event)
      rescue
        puts "WARN: Unable to get access key from context while trying to associate \
access key with state."
        return false
      end

      begin
        association = TripItAuthState.new(tripit_token: token,
                                          tripit_token_secret: token_secret,
                                          access_key: access_key)
        association.save
        return true
      rescue Exception => e
        TripIt.logger.error("Unable to save auth state: #{e}")
        return false
      end
    end

    # Gets an access key from a given state ID
    def self.get_access_key_from_state(token:)
      begin
        results = TripItAuthState.where(tripit_token: token)
        return nil if results.nil? or results.count == 0
        results.first.access_key
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripIt.logger.warn("State associations table not created yet.")
        return nil
      end
    end

    def self.get_token_secret_from_state(token:)
      begin
        results = TripItAuthState.where(tripit_token: token)
        return nil if results.nil? or results.count == 0
        results.first.tripit_token_secret
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripIt.logger.warn("State associations table not created yet.")
        return nil
      end
    end

    def self.configure_aws!
      if ENV['APP_AWS_SECRET_ACCESS_KEY'].nil? or ENV['APP_AWS_ACCESS_KEY_ID'].nil?
        return false
      end
      begin
        ::Aws.config.update(
          credentials: ::Aws::Credentials.new(ENV['APP_AWS_ACCESS_KEY_ID'],
                                              ENV['APP_AWS_SECRET_ACCESS_KEY']))
        return true
      rescue Exception => e
        TripIt.logger.error("Unable to configure Aws: #{e}")
        return false
      end
    end
  end
end
