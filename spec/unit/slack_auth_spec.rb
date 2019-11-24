require 'spec_helper'
require 'ostruct'

describe "TripIt OAuth" do
  context 'Handling state associations' do
    it "Should save access keys with state IDs", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      fake_event = JSON.parse({
        requestContext: {
          identity: {
            apiKey: 'fake-key'
          }
        }
      }.to_json)
      TripItAPI::Auth.associate_access_key_to_state_id!(event: fake_event,
                                                       state_id: 'fake-state-id')
      expect(TripItAPI::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
        .to eq 'fake-key'
    end
  end

  context 'Handling tokens' do
    it "Should give me an error message Retrieving tokens while not authenticated", :unit do
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
      expect(TripItAPI::Auth::get_tripit_token(event: fake_event)).to eq expected_response
    end

    it "Should persist tokens with their associated API keys", :unit do
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
      expect(TripItAPI::Auth::put_tripit_token(access_key: 'fake-key',
                                             tripit_token: 'fake')).to be true
      expect(TripItAPI::Auth::get_tripit_token(event: fake_event)).to eq expected_get_response
    end
  end
  context "We aren't authenticated yet" do
    it "Should give the user an auth init prompt without providing a workspace", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      expect(SecureRandom).to receive(:hex).and_return('fake-state-id')
      fake_event = JSON.parse({
        queryStringParameters: {
          workspace: 'fake'
        },
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
https://fake.tripit.com/oauth/authorize?client_id=fake&\
scope=users.profile:read,users.profile:write&\
redirect_uri=https://example.fake/develop/callback&\
state=fake-state-id"
      expected_response = {
        statusCode: 200,
        body: { status: 'ok', message: expected_message }.to_json
      }
      expect(TripItAPI::Auth::begin_authentication_flow(fake_event,
                                                       client_id: 'fake'))
        .to eq expected_response
      expect(TripItAPI::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
        .to eq 'fake-key'
    end

    it "Should give the user an auth init prompt when a workspace is provided", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      expect(SecureRandom).to receive(:hex).and_return('fake-state-id')
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
https://tripit.com/oauth/authorize?client_id=fake&\
scope=users.profile:read,users.profile:write&\
redirect_uri=https://example.fake/develop/callback&\
state=fake-state-id"
      expected_response = {
        statusCode: 200,
        body: { status: 'ok', message: expected_message }.to_json
      }
      expect(TripItAPI::Auth::begin_authentication_flow(fake_event,
                                                       client_id: 'fake'))
        .to eq expected_response
      expect(TripItAPI::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
        .to eq 'fake-key'
    end

    it "Should short-circuit this process if the user already has a token", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      TripItAPI::Auth.put_tripit_token(access_key: 'fake-key', tripit_token: 'fake')
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
      expect(TripItAPI::Auth.begin_authentication_flow(fake_event,
                                                      client_id: 'fake'))
          .to eq expected_response
    end
    it "Should avoid short-circuiting if we tell it to", :unit do
        Helpers::Aws::DynamoDBLocal.drop_tables!
        expect(SecureRandom).to receive(:hex).and_return('fake-state-id')
        TripItAPI::Auth.put_tripit_token(access_key: 'fake-key-again', tripit_token: 'fake')
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
https://tripit.com/oauth/authorize?client_id=fake&\
scope=users.profile:read,users.profile:write&\
redirect_uri=https://example.fake/develop/callback&\
state=fake-state-id"
        expected_response = {
          statusCode: 200,
          body: { status: 'ok', message: expected_message }.to_json
        }
        expect(TripItAPI::Auth::begin_authentication_flow(fake_event,
                                                         client_id: 'fake'))
          .to eq expected_response
        expect(TripItAPI::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
          .to eq 'fake-key-again'
    end
  end

  context "We've been authenticated" do
    it "Should ok if I was able to get a token", :unit do
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
      allow(TripItAPI::TripIt::OAuth).to receive(:access).and_return(OpenStruct.new(
        body: {
          ok: true,
          access_token: 'fake-token',
          scope: 'read'
        }.to_json))
      allow(TripItAPI::Auth).to receive(:get_access_key_from_state).and_return('fake-key')
      expect(TripItAPI::Auth::handle_callback(fake_event)).to eq expected_response
    end
  end
end
