require 'tripit/core/api'

module SlackAPI
  module Slack
    module OAuth
      # Retrieve an OAuth token from a given code and client ID/secret.
      def self.access(client_id:, client_secret:, code:, redirect_uri:)
        params = {
          client_id: client_id,
          client_secret: client_secret,
          code: code,
          redirect_uri: redirect_uri
        }
        SlackAPI::Slack::API.post_to(endpoint: 'oauth.access',
                                     content_type: 'application/x-www-formencoded',
                                     params: params)
      end

      def self.token_expired?(token:)
        response = SlackAPI::Slack::API.get_from(endpoint: 'auth.test',
                                                 params: { token: token })
        json = JSON.parse(response.body, symbolize_names: true)
        json[:ok] == false and json[:error] == 'invalid_auth'
      end
    end
  end
end

