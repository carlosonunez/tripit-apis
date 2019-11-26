require 'tripit/core/oauth'

module Helpers
  module TripIt
    module OAuth
      module Authenticated
        def self.generate_test_headers(uri)
          ::TripIt::Core::OAuth::Authenticated.generate_headers(
            uri: uri,
            consumer_key: 'fake-client-id',
            consumer_secret: 'fake-client-secret',
            nonce: 'fake-nonce',
            token: 'fake-token',
            token_secret: 'fake-token-secret',
            timestamp: '123'
          )
        end
      end
    end
  end
end
