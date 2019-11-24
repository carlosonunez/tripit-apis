require 'json'

module Helpers
  module Unit
    module Aws
      module ApiGateway
        def self.return_200(body:)
          {
            :statusCode => 200,
            :body => body
          }.to_json
        end
      end
    end
  end
end

