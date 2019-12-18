require 'tripit/core/api'

module TripIt
  module Core
    class Trip
      attr_accessor :data

      def initialize(id, token, secret)
        response = TripIt::Core::API::V1.get_from(
          endpoint: "get/trip/id/#{id}",
          params: {
            include_objects: true
          },
          token: token,
          token_secret: secret
        )
        if response.code != 200
          puts "WARN: Unable to get data for ID #{id}: #{response.body}"
        end
        @data = JSON.parse(response.body, symbolize_names: true)
      end

      def cache(id)
        @cached_data[id] = @data
      end
    end
  end
end
