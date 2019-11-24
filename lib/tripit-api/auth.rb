require 'aws-sdk-dynamodb'
require 'tripit-api/aws_helpers/api_gateway'
require 'tripit-api/tripit'
require 'logger'
require 'securerandom'
require 'dynamoid'

module TripItAPI
  module Auth
    class TripItToken
      Dynamoid.configure do |config|
        config.namespace = "tripit_auth"
        config.logger.level = Logger::FATAL
      end

      include Dynamoid::Document
      table name: :tokens, key: :access_key, read_capacity: 2, write_capacity: 2
      field :access_key
      field :tripit_token
    end

    class TripItAuthState
      Dynamoid.configure do |config|
        config.namespace = "tripit_auth_state"
        config.logger.level = Logger::FATAL
      end

      include Dynamoid::Document
      table name: :state_associations, key: :state_id, read_capacity: 2, write_capacity: 2
      field :access_key
      field :state_id
    end
=begin
    Handle TripIt OAuth callbacks.
=end
    def self.handle_callback(event)
      if !self.configure_aws!
        return TripItAPI::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      parameters = event['queryStringParameters']
      code = parameters['code']
      state_id = parameters['state']
      error = parameters['error']
      if !error.nil?
        return TripItAPI::AWSHelpers::APIGateway.unauthenticated(
          message: "User denied access to this app.")
      elsif code.nil? and state_id.nil?
        return TripItAPI::AWSHelpers::APIGateway.error(
          message: "TripIt didn't send a code or state_id upon calling back.")
      else
        callback_url = 'https://' + TripItAPI::AWSHelpers::APIGateway.get_endpoint(event) + \
          event['requestContext']['path']
        token_response = TripItAPI::TripIt::OAuth.access(client_id: ENV['TRIPIT_APP_CLIENT_ID'],
                                                       client_secret: ENV['TRIPIT_APP_CLIENT_SECRET'],
                                                       redirect_uri: callback_url,
                                                       code: code)
        if token_response.body.nil?
          return TripItAPI::AWSHelpers::APIGateway.error(
            message: 'Unable to get TripIt token.')
        end
        token_response_json = JSON.parse(token_response.body)
        if !token_response_json['ok'].nil? and !token_response_json['ok']
          return TripItAPI::AWSHelpers::APIGateway.unauthenticated(
            message: "Token request failed: #{token_response_json['error']}"
          )
        end
        token = token_response_json['access_token']
        access_key_from_state = self.get_access_key_from_state(state_id: state_id)
        if access_key_from_state.nil?
          return TripItAPI::AWSHelpers::APIGateway.error(
            message: "No access key exists for this state ID: #{state_id}")
        end
        if self.put_tripit_token(access_key: access_key_from_state, tripit_token: token)
          return TripItAPI::AWSHelpers::APIGateway.ok
        else
          return TripItAPI::AWSHelpers::APIGateway.error(message: "Unable to save TripIt token.")
        end
      end
    end

=begin
    Provide a first step for the authentication flow.
=end
    def self.begin_authentication_flow(event, client_id:)
      if !self.configure_aws!
        return TripItAPI::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      if !self.reauthenticate?(event: event) and self.has_token? event: event
        return TripItAPI::AWSHelpers::APIGateway.ok(message: 'You already have a token.')
      end
      scopes_csv = ENV['TRIPIT_APP_CLIENT_SCOPES'] || "users.profile:read,users.profile:write"
      redirect_uri = "https://#{TripItAPI::AWSHelpers::APIGateway.get_endpoint(event)}/callback"
      workspace = self.get_workspace(event)
      state_id = self.generate_state_id
      if workspace.nil?
        workspace_url = "tripit.com"
      else
        workspace_url = "#{workspace}.tripit.com"
      end
      tripit_authorization_uri = [
        "https://#{workspace_url}/oauth/authorize?client_id=#{client_id}",
        "scope=#{scopes_csv}",
        "redirect_uri=#{redirect_uri}",
        "state=#{state_id}"
      ].join '&'
      message = "You will need to authenticate into TripIt first; click on or \
copy/paste this URL to get started: #{tripit_authorization_uri}"
      if !self.associate_access_key_to_state_id!(event: event,
                                                 state_id: state_id)
        return TripItAPI::AWSHelpers::APIGateway.error(
          message: "Couldn't map state to access key.")
      end
      return TripItAPI::AWSHelpers::APIGateway.ok(message: message)
    end

    # Retrives a TripIt OAuth token from a API Gateway key
    def self.get_tripit_token(event:)
      if !self.configure_aws!
        return TripItAPI::AWSHelpers::APIGateway.error(
          message: 'Please set APP_AWS_ACCESS_KEY and APP_AWS_SECRET_KEY')
      end
      access_key = self.get_access_key_from_event(event)
      if access_key.nil?
        return TripItAPI::AWSHelpers::APIGateway.error(message: 'Access key missing.')
      end
      tripit_token = self.get_tripit_token_from_access_key(access_key)
      if tripit_token.nil?
        return TripItAPI::AWSHelpers::APIGateway.not_found(
          message: 'No token exists for this access key.')
      end
      TripItAPI::AWSHelpers::APIGateway.ok(
        additional_json: { token: tripit_token })
    end

    private
    def self.get_workspace(event)
      begin
        event['queryStringParameters']['workspace']
      rescue
        return nil
      end
    end

    def self.generate_state_id
      SecureRandom.hex
    end

    def self.get_access_key_from_event(event)
      event['requestContext']['identity']['apiKey']
    end

    def self.get_tripit_token_from_access_key(access_key)
      begin
        results = TripItToken.where(access_key: access_key)
        return nil if results.count == 0
        results.first.tripit_token
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripItAPI.logger.warn("TripIt tokens table not created yet.")
        return nil
      end
    end

    # Puts a new token and API key into DynamoDB
    def self.put_tripit_token(access_key:, tripit_token:)
      begin
        mapping = TripItToken.new(access_key: access_key,
                                 tripit_token: tripit_token)
        mapping.save
        return true
      rescue Dynamoid::Errors::ConditionalCheckFailedException
        puts "WARN: This access key already has a TripIt token. We will check for \
existing tokens and provide a refresh mechanism in a future commit."
        return true
      rescue Exception => e
        TripItAPI.logger.error("We weren't able to save this token: #{e}")
        return false
      end
    end

    def self.has_token?(event:)
      begin
        access_key = self.get_access_key_from_event(event)
        results = TripItToken.where(access_key: access_key)
        return nil if results.nil? or results.count == 0
        !results.first.tripit_token.nil?
      rescue Exception => e
        TripItAPI.logger.warn("Error while querying for an existing token; beware stranger tings: #{e}")
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
    # table mapping access keys to `state_id`s.
    #
    # This introduces a security vulnerability where someone can change
    # another user's TripIt token by invoking
    # /callback (a public method, as required by TripIt OAuth) with a correct
    # state ID. We will need to fix that at some point.
    def self.associate_access_key_to_state_id!(event:, state_id:)
      begin
        access_key = self.get_access_key_from_event(event)
      rescue
        puts "WARN: Unable to get access key from context while trying to associate \
access key with state."
        return false
      end

      begin
        association = TripItAuthState.new(state_id: state_id,
                                         access_key: access_key)
        association.save
        return true
      rescue Exception => e
        TripItAPI.logger.error("Unable to save auth state: #{e}")
        return false
      end
    end

    # Gets an access key from a given state ID
    def self.get_access_key_from_state(state_id:)
      begin
        results = TripItAuthState.where(state_id: state_id)
        return nil if results.nil? or results.count == 0
        results.first.access_key
      rescue Aws::DynamoDB::Errors::ResourceNotFoundException
        TripItAPI.logger.warn("State associations table not created yet.")
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
        TripItAPI.logger.error("Unable to configure Aws: #{e}")
        return false
      end
    end
  end
end
