require 'httparty'
require 'tripit/core/oauth'

module TripIt
  module Core
    module API
      module V1
        def self.get_from(endpoint:, token:, token_secret:, params: nil)
          base_uri = "https://api.tripit.com/v1"
          # This makes me so sad.
          # Instead of using query parameters, TripIt requires that we
          # put all of the parameters as paths in the URL.
          # Example: Instead of /v1/get/flight?includeObjects=true&format=json,
          # this API wants: /v1/get/flight/includeObjects/true/format/json.
          #
          # That's why this is namespaced within a `V1` module.
          #
          # I would like for this to change
          # but I know it won't
          # And so I will remain sad
          # Bad haiku
          _ = params[:format].delete if !params.nil? and params.key(:format)
          params_string = ""
          if !params.nil?
            params_string = params.sort.to_h.map{|k,v| "#{k}/#{v}"}.join('/')
          end
          suffix =
            "#{endpoint.gsub(/^\//,'')}/#{params_string}/format/json".gsub(/\/{1,}/,'/')
          uri = "#{base_uri}/#{suffix}"
          puts "DEBUG: URI to get: #{uri}"
          auth_header = TripIt::Core::OAuth::Authenticated.generate_headers(
            uri: uri,
            consumer_key: ENV['TRIPIT_APP_CLIENT_ID'],
            consumer_secret: ENV['TRIPIT_APP_CLIENT_SECRET'],
            nonce: SecureRandom.hex,
            token: token,
            token_secret: token_secret,
            timestamp: Time.now.to_i
          )
          HTTParty.get(uri, headers: { 'Authorization': auth_header })
        end
      end
    end
  end
end

