require 'base64'
require 'cgi'
require 'openssl'
require 'securerandom'
require 'tripit/core/api'

module TripIt
  module Core
    module OAuth
      module Request
        def self.generate_headers(consumer_key:,
                                  consumer_secret:,
                                  nonce:,
                                  timestamp:)
          uri = "https://api.tripit.com/oauth/request_token"
          signature =  TripIt::Core::OAuth.generate_signature(
            uri: uri,
            method: 'GET',
            consumer_key: consumer_key,
            consumer_secret: consumer_secret,
            nonce: nonce,
            timestamp: timestamp)
          return TripIt::Core::OAuth.generate_auth_header(
            realm: uri,
            signature: signature,
            headers:  {
              oauth_consumer_key: consumer_key,
              oauth_nonce: nonce,
              oauth_timestamp: timestamp.to_s,
              oauth_signature_method: 'HMAC-SHA1',
              oauth_version: '1.0',
            })
        end

        def self.get_tokens
          ['TRIPIT_APP_CLIENT_ID','TRIPIT_APP_CLIENT_SECRET'].each {|required|
            raise "Parameter missing: #{required}" if ENV[required].nil?
          }
          timestamp = Time.now.to_i
          auth_header = self.generate_headers(
            consumer_key: ENV['TRIPIT_APP_CLIENT_ID'],
            consumer_secret: ENV['TRIPIT_APP_CLIENT_SECRET'],
            nonce: SecureRandom.hex,
            timestamp:  timestamp)
          url = 'https://api.tripit.com/oauth/request_token'
          response = HTTParty.get(url, {
            headers: { 'Authorization': auth_header }
          })
          if response.code != 200
            raise "Failed to get request token: #{response.body}"
          end
          token_data = {}
          response.body.split('&').each do |attribute|
            key = attribute.split('=').first
            value = attribute.split('=').last
            case key
            when 'oauth_token'
              token_data[:token] = value
            when 'oauth_token_secret'
              token_data[:token_secret] = value
            end
          end
          token_data
        end
      end

      module Access
        def self.generate_headers(consumer_key:,
                                  consumer_secret:,
                                  nonce:,
                                  token:,
                                  token_secret:,
                                  timestamp:)
          uri = "https://api.tripit.com/oauth/access_token"
          signature =  TripIt::Core::OAuth.generate_signature(
            uri: uri,
            method: 'GET',
            consumer_key: consumer_key,
            consumer_secret: consumer_secret,
            token: token,
            token_secret: token_secret,
            nonce: nonce,
            timestamp: timestamp)
          return TripIt::Core::OAuth.generate_auth_header(
            realm: uri,
            signature: signature,
            headers:  {
              oauth_consumer_key: consumer_key,
              oauth_token: token,
              oauth_nonce: nonce,
              oauth_timestamp: timestamp.to_s,
              oauth_signature_method: 'HMAC-SHA1',
              oauth_version: '1.0',
            })
        end

        def self.get_tokens(request_token:, request_token_secret:)
          ['TRIPIT_APP_CLIENT_ID','TRIPIT_APP_CLIENT_SECRET'].each {|required|
            raise "Parameter missing: #{required}" if ENV[required].nil?
          }
          timestamp = Time.now.to_i
          auth_header = self.generate_headers(
            consumer_key: ENV['TRIPIT_APP_CLIENT_ID'],
            consumer_secret: ENV['TRIPIT_APP_CLIENT_SECRET'],
            nonce: SecureRandom.hex,
            token: request_token,
            token_secret: request_token_secret,
            timestamp:  timestamp)
          url = 'https://api.tripit.com/oauth/access_token'
          response = HTTParty.get(url, {
            headers: { 'Authorization': auth_header }
          })
          if response.code != 200
            raise "Failed to get request token: #{response.body}"
          end
          token_data = {}
          response.body.split('&').each do |attribute|
            key = attribute.split('=').first
            value = attribute.split('=').last
            case key
            when 'oauth_token'
              token_data[:token] = value
            when 'oauth_token_secret'
              token_data[:token_secret] = value
            end
          end
          token_data
        end
      end

      # Retrieve an OAuth token from a given code and client ID/secret.
      def self.access(client_id:, client_secret:, code:, redirect_uri:)
        params = {
          client_id: client_id,
          client_secret: client_secret,
          code: code,
          redirect_uri: redirect_uri
        }
        TripIt::Core::API.post_to(endpoint: 'oauth.access',
                                  content_type: 'application/x-www-formencoded',
                                  params: params)
      end

      def self.token_expired?(token:)
        response = TripIt::Core::API.get_from(endpoint: 'auth.test',
                                              params: { token: token })
        json = JSON.parse(response.body, symbolize_names: true)
        json[:ok] == false and json[:error] == 'invalid_auth'
      end

      def self.generate_auth_header(realm:, headers:, signature:)
        [
          "OAuth realm=\"#{realm}\"",
          headers.sort.to_h.map{|key,value| "#{key}=\"#{value}\""}.join(','),
          "oauth_signature=\"#{CGI.escape(signature)}\""
        ].join(',')
      end

      def self.generate_signature(method:, uri:, consumer_key:,
                                  nonce:, timestamp:, token: nil,
                                  token_secret: nil, consumer_secret:)
        params = {
          oauth_consumer_key: consumer_key,
          oauth_nonce: nonce,
          oauth_signature_method: 'HMAC-SHA1',
          oauth_timestamp: timestamp,
          oauth_version: '1.0'
        }
        if !token.nil?
          params[:oauth_token] = token
        end
        params = params.sort.to_h
        encrypt_key = "#{consumer_secret}&" # This isn't in the TripIt documentation!
        if !token_secret.nil?
          encrypt_key += token_secret
        end
        require 'pp'
        params_serialized = params.map{|key,value| "#{key}=#{value}"}.join('&')
        sig_base_string = "#{method}&#{CGI.escape uri}&#{CGI.escape params_serialized}"
        raw_signature = OpenSSL::HMAC.digest('SHA1', encrypt_key, sig_base_string)
        encoded_signature = Base64.encode64(raw_signature).strip
        return encoded_signature
      end
    end
  end
end

