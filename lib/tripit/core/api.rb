require 'httparty'

module TripIt
  module Core
    module API
      # Issues a GET request against a TripIt API method.
      def self.get_from(endpoint:, token: nil, params: {}, content_type: 'application/json')
        params[:token] = token if !token.nil?
        HTTParty.get("https://slack.com/api/#{endpoint}",
                     query: params,
                     headers: { 'Content-Type': content_type })
      end

      def self.post_to(endpoint:, token: nil, params: {}, body: nil, content_type: 'application/x-www-formencoded')
        params[:token] = token if !token.nil?
        HTTParty.post("https://slack.com/api/#{endpoint}",
                      query: params,
                      body: body,
                      headers: { 'Content-Type': content_type })
      end
    end
  end
end

