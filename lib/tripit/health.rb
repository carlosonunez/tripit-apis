require 'json'
require 'tripit/aws_helpers/api_gateway'

module TripIt
  class Health
    def self.ping
      TripIt::AWSHelpers::APIGateway.return_200 body: "sup dawg"
    end
  end
end
