require 'json'
require 'tripit-api/aws_helpers/api_gateway'

module TripIt
  class Health
    def self.ping
      AWSHelpers::APIGateway.return_200 body: "sup dawg"
    end
  end
end
