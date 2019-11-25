require 'spec_helper'
require 'cgi'
require 'base64'

describe "Authenticating into TripIt" do
  context "When we're going to start authenticating" do
    it "Should give the user an auth init prompt", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      fake_event = JSON.parse({
        requestContext: {
          path: '/develop/auth',
          identity: {
            apiKey: 'fake-key'
          }
        },
        headers: {
          Host: 'example.fake'
        }
      }.to_json)
      expected_message = "You will need to authenticate into TripIt first; \
click on or copy/paste this URL to get started: \
https://www.tripit.com/oauth/authorize?oauth_token=fake-token&\
oauth_callback=https://example.fake/develop/callback"
      expected_response = {
        statusCode: 200,
        body: { status: 'ok', message: expected_message }.to_json
      }
      expect(TripIt::Core::OAuth).to receive(:get_request_tokens)
        .and_return({ token: 'fake-token', token_secret: 'fake-token-secret' })
      expect(TripIt::Auth::begin_authentication_flow(fake_event))
        .to eq expected_response
      expect(TripIt::Auth.get_access_key_from_state(token: 'fake-token'))
        .to eq 'fake-key'
      expect(TripIt::Auth.get_token_secret_from_state(token: 'fake-token'))
        .to eq 'fake-token-secret'
    end

    it "Should short-circuit this process if the user already has a token", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      TripIt::Auth.put_tripit_token(access_key: 'fake-key', tripit_token: 'fake')
      fake_event = JSON.parse({
        requestContext: {
          path: '/develop/auth',
          identity: {
            apiKey: 'fake-key'
          }
        },
        headers: {
          Host: 'example.fake'
        }
      }.to_json)
      expected_response = {
        statusCode: 200,
        body: { status: 'ok', message: 'You already have a token.' }.to_json
      }
      expect(TripIt::Auth.begin_authentication_flow(fake_event)).to eq expected_response
    end

    it "Should avoid short-circuiting if we tell it to", :unit do
        Helpers::Aws::DynamoDBLocal.drop_tables!
        TripIt::Auth.put_tripit_token(access_key: 'fake-key-again', tripit_token: 'fake')
        fake_event = JSON.parse({
          requestContext: {
            path: '/develop/auth',
            identity: {
              apiKey: 'fake-key-again'
            }
          },
          queryStringParameters: {
            reauthenticate: 'true'
          },
          headers: {
            Host: 'example.fake'
          }
        }.to_json)
        expected_message = "You will need to authenticate into TripIt first; \
click on or copy/paste this URL to get started: \
https://www.tripit.com/oauth/authorize?\
oauth_token=fake-token&\
oauth_callback=https://example.fake/develop/callback"
        expected_response = {
          statusCode: 200,
          body: { status: 'ok', message: expected_message }.to_json
        }
        expect(TripIt::Core::OAuth).to receive(:get_request_tokens)
          .and_return({ token: 'fake-token', token_secret: 'fake-token-secret' })
        expect(TripIt::Auth::begin_authentication_flow(fake_event))
          .to eq expected_response
    end
  end

  context "We've been authenticated" do
    it "Should ok if I was able to get a token", :wip do
      expected_response = {
        statusCode: 200,
        body: { status: 'ok' }.to_json
      }
      fake_event = JSON.parse({
        requestContext: {
          path: '/develop/callback',
          identity: {
            apiKey: 'fake-key'
          }
        },
        queryStringParameters: {
          code: 'fake-code',
          state: 'fake-state'
        },
        headers: {
          Host: 'example.host'
        }
      }.to_json)
      allow(TripIt::Auth).to receive(:get_access_key_from_state).and_return('fake-key')
      expect(TripIt::Auth::handle_callback(fake_event)).to eq expected_response
    end
  end
  context 'Handling state associations' do
    it "Should save access keys with state IDs", :wip do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      fake_event = JSON.parse({
        requestContext: {
          identity: {
            apiKey: 'fake-key'
          }
        }
      }.to_json)
      TripIt::Auth.associate_access_key_to_state_id!(event: fake_event,
                                                       state_id: 'fake-state-id')
      expect(TripIt::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
        .to eq 'fake-key'
    end
  end

  context 'Handling tokens' do
    it "Should give me an error message Retrieving tokens while not authenticated", :wip do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      fake_event = JSON.parse({
        requestContext: {
          identity: {
            apiKey: 'fake-key'
          }
        }
      }.to_json)
      expected_response = {
        statusCode: 404,
        body: { status: 'error', message: 'No token exists for this access key.' }.to_json
      }
      expect(TripIt::Auth::get_tripit_token(event: fake_event)).to eq expected_response
    end

    it "Should persist tokens with their associated API keys", :wip do
      fake_event = JSON.parse({
        requestContext: {
          identity: {
            apiKey: 'fake-key'
          }
        }
      }.to_json)
      expected_get_response = {
        statusCode: 200,
        body: { status: 'ok', token: 'fake' }.to_json
      }
      expect(TripIt::Auth::put_tripit_token(access_key: 'fake-key',
                                             tripit_token: 'fake')).to be true
      expect(TripIt::Auth::get_tripit_token(event: fake_event)).to eq expected_get_response
    end
  end
end
