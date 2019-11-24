require 'base64'
require 'cgi'
require 'openssl'
require 'tripit/core/api'

module TripIt
  module Core
    module OAuth
      def self.generate_request_auth_headers(consumer_key:,
                                             consumer_secret:,
                                             nonce:,
                                             timestamp:)
        signature = self.generate_signature_for_request_token(
          consumer_key: consumer_key,
          consumer_secret: consumer_secret,
          nonce: nonce,
          timestamp: timestamp)
        headers = {
          realm: 'https://api.tripit.com/oauth/request_token',
          oauth_consumer_key: consumer_key,
          oauth_nonce: nonce,
          oauth_timestamp: timestamp,
          oauth_signature_method: 'HMAC-SHA1',
          oauth_version: '1.0',
          oauth_signature: signature,
        }
        return "OAuth " + headers.map{|k,v| "#{k}=#{Base64.encode64(v)}"}.join(',')
      end

      # Since this uses OAuth v1, we need to generate a signature by hand.
      def self.generate_signature_for_request_token(consumer_key:, consumer_secret:, nonce:, timestamp:)
        method = 'GET'
        uri = "https://api.tripit.com/oauth/request_token"
        params = {
          oauth_consumer_key: consumer_key,
          oauth_nonce: nonce,
          oauth_signature_method: 'HMAC-SHA1',
          oauth_timestamp: timestamp,
          oauth_version: '1.0'
        }
        params_serialized = params.map{|key,value| "#{key}=#{value}"}.join('&')
        sig_base_string = "#{method}&#{CGI.escape uri}&#{CGI.escape params_serialized}"
        encrypt_key = "#{consumer_secret}&" # This isn't in the TripIt documentation!
        raw_signature = OpenSSL::HMAC.digest('SHA1', encrypt_key, sig_base_string)
        encoded_signature = Base64.encode64(raw_signature).strip
        return encoded_signature
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
    end
  end
end

