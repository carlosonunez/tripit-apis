require 'net/http'

module Helpers
  module Integration
    module HTTP
      # TODO: This should probably set the global var to avoid coupling.
      def self.get_endpoint
        return $api_gateway_url if !$api_gateway_url.nil?
        seconds_to_wait = ENV['API_GATEWAY_URL_FETCH_TIMEOUT'] || 60
        puts "Waiting up to #{seconds_to_wait} seconds for endpoint to become available..."
        attempts = 1
        while attempts <= seconds_to_wait
          begin
            return Helpers::Integration::SharedSecrets.read_secret secret_name: 'endpoint_name'
          rescue
            attempts += 1
            sleep 1
          end
        end
        raise "Secret 'endpoint_name' not found."
      end
    end
  end
end

