require 'spec_helper'
require 'cgi'
require 'base64'

describe "TripIt OAuth" do
  context "OAuth v1 request tokens" do
    it "Should yield a correct signature", :unit do
      expected_signature = "wr9/w0ruXKUD6KZvd2QmKX1KYaA="
      oauth_consumer_key = ENV['TRIPIT_APP_CLIENT_ID'] || raise("No client ID found.")
      oauth_consumer_secret = ENV['TRIPIT_APP_CLIENT_SECRET'] || raise("No client secret found.")
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = '1574621346'
      expect(
        TripIt::Core::OAuth.generate_signature_for_request_token(consumer_key: oauth_consumer_key,
                                                                 consumer_secret: oauth_consumer_secret,
                                                                 nonce: oauth_nonce,
                                                                 timestamp: oauth_timestamp))
        .to eq expected_signature
    end

    it "Should yield correct authorization headers", :unit do
      expected_signature = "wr9/w0ruXKUD6KZvd2QmKX1KYaA="
      oauth_consumer_key = ENV['TRIPIT_APP_CLIENT_ID'] || raise("No client ID found.")
      oauth_consumer_secret = ENV['TRIPIT_APP_CLIENT_SECRET'] || raise("No client secret found.")
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = '1574621346'
      expected_auth_headers_hash = {
        realm: 'https://api.tripit.com/oauth/request_token',
        oauth_consumer_key: oauth_consumer_key,
        oauth_nonce: oauth_nonce,
        oauth_timestamp: oauth_timestamp,
        oauth_signature_method: 'HMAC-SHA1',
        oauth_version: '1.0',
        oauth_signature: CGI.escape(expected_signature),
      }
      expected_auth_headers = "OAuth " + expected_auth_headers_hash.map {|key, value|
        "#{key}=#{value}"
      }.join(',')
      expect(TripIt::Core::OAuth.generate_request_auth_headers(consumer_key: oauth_consumer_key,
                                                               consumer_secret: oauth_consumer_secret,
                                                               nonce: oauth_nonce,
                                                               timestamp: oauth_timestamp))
        .to eq expected_auth_headers
    end

    it "Should give us a request token and secret", :unit do
      mocked_time = Time.parse("2019-11-24 14:39:41 -0600")
      fake_token='fake-token'
      fake_token_secret='fake-secret'
      mocked_response = double(HTTParty::Response,
                               body: "oauth_token=#{fake_token}&oauth_token_secret=#{fake_token_secret}",
                               code: 200)
      oauth_consumer_key = ENV['TRIPIT_APP_CLIENT_ID'] || raise("No client ID found.")
      oauth_consumer_secret = ENV['TRIPIT_APP_CLIENT_SECRET'] || raise("No client secret found.")
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = mocked_time.to_i
      uri_being_mocked = 'https://api.tripit.com/oauth/request_token'
      mocked_headers = TripIt::Core::OAuth.generate_request_auth_headers(
        consumer_key: oauth_consumer_key,
        consumer_secret: oauth_consumer_secret,
        nonce: oauth_nonce,
        timestamp: oauth_timestamp)
      expect(Time).to receive(:now).and_return(mocked_time)
      expect(SecureRandom).to receive(:hex).and_return(oauth_nonce)
      expect(HTTParty).to receive(:post)
        .with(uri_being_mocked, { headers: { 'Authorization': mocked_headers } })
        .and_return(mocked_response)
      expect(TripIt::Core::OAuth.get_request_tokens).to eq({
        token: fake_token,
        token_secret: fake_token_secret
      })
    end
  end

  context "We aren't authenticated yet" do
    it "Should give the user an auth init prompt", :unit do
      Helpers::Aws::DynamoDBLocal.drop_tables!
      ENV['TRIPIT_CONSUMER_PUBLIC_KEY'] = 'fake-key'
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
      expect(TripIt::Auth::begin_authentication_flow(fake_event,
                                                       client_id: 'fake'))
        .to eq expected_response
      expect(TripIt::Auth.get_access_key_from_state(oauth_token: 'fake-token'))
        .to eq 'fake-key'
      expect(TripIt::Auth.get_token_secret_from_state(oauth_token: 'fake-token'))
        .to eq 'fake-secret'
    end

    it "Should give the user an auth init prompt", :wip do
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
      expect(TripIt::Auth::begin_authentication_flow(fake_event,
                                                       client_id: 'fake'))
        .to eq expected_response
      expect(TripIt::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
        .to eq 'fake-key'
    end

    it "Should short-circuit this process if the user already has a token", :wip do
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
      expect(TripIt::Auth.begin_authentication_flow(fake_event,
                                                      client_id: 'fake'))
          .to eq expected_response
    end
    it "Should avoid short-circuiting if we tell it to", :wip do
        Helpers::Aws::DynamoDBLocal.drop_tables!
        expect(SecureRandom).to receive(:hex).and_return('fake-state-id')
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
https://tripit.com/oauth/authorize?client_id=fake&\
scope=users.profile:read,users.profile:write&\
redirect_uri=https://example.fake/develop/callback&\
state=fake-state-id"
        expected_response = {
          statusCode: 200,
          body: { status: 'ok', message: expected_message }.to_json
        }
        expect(TripIt::Auth::begin_authentication_flow(fake_event,
                                                         client_id: 'fake'))
          .to eq expected_response
        expect(TripIt::Auth.get_access_key_from_state(state_id: 'fake-state-id'))
          .to eq 'fake-key-again'
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
      allow(TripIt::Core::OAuth).to receive(:access).and_return(OpenStruct.new(
        body: {
          ok: true,
          access_token: 'fake-token',
          scope: 'read'
        }.to_json))
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
