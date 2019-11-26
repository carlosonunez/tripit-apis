require 'json'

module TripIt
  module AWSHelpers
    module APIGateway
      module Events
        def self.get_param(event:,param:)
          event.dig('queryStringParameters', param)
        end
        def self.get_access_key(event)
          event['requestContext']['identity']['apiKey']
        end
      end
=begin
      Retrieves the endpoint from a request, optionally with a part of its path removed.
=end
      def self.get_endpoint(event, path_to_remove: '/auth')
        # TODO: Fix TypeError Hash into String errror from API Gateway.
        path = event['requestContext']['path'] || raise("Path not found in event.")
        path_subbed = path.gsub!(path_to_remove,'')
        host = event['headers']['Host'] || raise("Host not found in event.")
        "#{host}#{path_subbed}"
      end

      def self.ok(message: nil, additional_json: nil)
        if message.nil? and additional_json.nil?
          self.return_200(json: { status: 'ok' })
        elsif !message.nil?
          self.return_200(json: { status: 'ok', message: message })
        else
          json = { status: 'ok' }.merge(additional_json)
          self.return_200(json: json)
        end
      end

      def self.error(message:)
        self.return_422(body: message)
      end

      def self.not_found(message:)
        self.return_404(body: message)
      end

      def self.unauthenticated(message: nil)
        if message.nil?
          self.return_403(body: 'Access denied.')
        else
          self.return_403(body: message)
        end
      end

      private
      def self.send_response(code:, payload:)
        raise "Payload must be a Hash" if !payload.nil? and payload.class != Hash
        {
          :statusCode => code,
          :body => payload.to_json
        }
      end

      def self.return_200(body: nil, json: {})
        raise "JSON can't be empty" if body.nil? and json.empty?
        if !json.empty?
          self.send_response(code: 200, payload: json)
        else
          self.send_response(code: 200, payload: { message: body })
        end
      end

      def self.return_403(body:)
        self.send_response(code: 403, payload: { status: 'error', message: body })
      end

      def self.return_404(body:)
        self.send_response(code: 404, payload: { status: 'error', message: body })
      end

      def self.return_422(body:)
        self.send_response(code: 422, payload: { status: 'error', message: body })
      end
    end
  end
end
