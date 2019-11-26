require 'spec_helper'

describe "TripIt OAuth methods" do
  context 'When retrieving request tokens' do
    it "Should yield correct authorization headers", :unit do
      expected_signature = "h6Azudvr61sWzIoqJbU8TVS1Lhw="
      oauth_consumer_key = 'fake-client-id'
      oauth_consumer_secret = 'fake-client-secret'
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = '123'
      uri = 'https://api.tripit.com/oauth/request_token'
      expected_auth_headers_hash = {
        oauth_consumer_key: oauth_consumer_key,
        oauth_nonce: oauth_nonce,
        oauth_timestamp: oauth_timestamp,
        oauth_signature_method: 'HMAC-SHA1',
        oauth_version: '1.0'
      }
      expected_auth_headers = "OAuth realm=\"#{uri}\"," + \
        expected_auth_headers_hash.sort.to_h.map {|key, value| "#{key}=\"#{value}\""}.join(',')
      expected_auth_headers += ",oauth_signature=\"#{CGI.escape(expected_signature)}\""
      expect(TripIt::Core::OAuth::Request.generate_headers(consumer_key: oauth_consumer_key,
                                                           consumer_secret: oauth_consumer_secret,
                                                           nonce: oauth_nonce,
                                                           timestamp: oauth_timestamp))
        .to eq expected_auth_headers
    end

    it "Should give us a request token and secret", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      fake_token='fake-token'
      fake_token_secret='fake-secret'
      mocked_response = double(HTTParty::Response,
                               body: "oauth_token=#{fake_token}&oauth_token_secret=#{fake_token_secret}",
                               code: 200)
      oauth_consumer_key = 'fake-client-id'
      oauth_consumer_secret = 'fake-client-secret'
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = mocked_time.to_i
      uri_being_mocked = 'https://api.tripit.com/oauth/request_token'
      mocked_headers = TripIt::Core::OAuth::Request.generate_headers(
        consumer_key: oauth_consumer_key,
        consumer_secret: oauth_consumer_secret,
        nonce: oauth_nonce,
        timestamp: oauth_timestamp)
      expect(Time).to receive(:now).and_return(mocked_time)
      expect(SecureRandom).to receive(:hex).and_return(oauth_nonce)
      expect(HTTParty).to receive(:get)
        .with(uri_being_mocked, { headers: { 'Authorization': mocked_headers } })
        .and_return(mocked_response)
      expect(TripIt::Core::OAuth::Request.get_tokens).to eq({
        token: fake_token,
        token_secret: fake_token_secret
      })
    end
  end

  context 'When retrieving access tokens' do
    it "Should yield correct authorization headers", :unit do
      oauth_consumer_key = 'fake-client-id'
      oauth_consumer_secret = 'fake-client-secret'
      oauth_token = 'fake-token'
      oauth_token_secret = 'fake-token-secret'
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = '123'
      expected_signature = "Gfs0FXIZZm07QMYjPr61yKFgGLk="
      uri = 'https://api.tripit.com/oauth/access_token'
      expected_auth_headers_hash = {
        oauth_consumer_key: oauth_consumer_key,
        oauth_nonce: oauth_nonce,
        oauth_timestamp: oauth_timestamp,
        oauth_signature_method: 'HMAC-SHA1',
        oauth_version: '1.0',
        oauth_token: oauth_token
      }
      expected_auth_headers = "OAuth realm=\"#{uri}\"," + \
        expected_auth_headers_hash.sort.to_h.map {|key, value| "#{key}=\"#{value}\""}.join(',')
      expected_auth_headers += ",oauth_signature=\"#{CGI.escape(expected_signature)}\""
      expect(TripIt::Core::OAuth::Access.generate_headers(consumer_key: oauth_consumer_key,
                                                          consumer_secret: oauth_consumer_secret,
                                                          nonce: oauth_nonce,
                                                          token: oauth_token,
                                                          token_secret: oauth_token_secret,
                                                          timestamp: oauth_timestamp))
        .to eq expected_auth_headers
    end
    it "Should give us an authenticated access token and secret", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      fake_token='fake-token'
      fake_token_secret='fake-secret'
      fake_request_token='fake-request-token'
      fake_request_token_secret='fake-request-token-secret'
      mocked_response = double(HTTParty::Response,
                               body: "oauth_token=#{fake_token}&oauth_token_secret=#{fake_token_secret}",
                               code: 200)
      oauth_consumer_key = 'fake-client-id'
      oauth_consumer_secret = 'fake-client-secret'
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = mocked_time.to_i
      uri_being_mocked = 'https://api.tripit.com/oauth/access_token'
      mocked_headers = TripIt::Core::OAuth::Access.generate_headers(
        consumer_key: oauth_consumer_key,
        consumer_secret: oauth_consumer_secret,
        nonce: oauth_nonce,
        token: fake_request_token,
        token_secret: fake_request_token_secret,
        timestamp: oauth_timestamp)
      expect(Time).to receive(:now).and_return(mocked_time)
      expect(SecureRandom).to receive(:hex).and_return(oauth_nonce)
      expect(HTTParty).to receive(:get)
        .with(uri_being_mocked, { headers: { 'Authorization': mocked_headers } })
        .and_return(mocked_response)
      token_data =
        TripIt::Core::OAuth::Access.get_tokens(request_token: fake_request_token,
                                              request_token_secret: fake_request_token_secret)
      expect(token_data).to eq({
        token: fake_token,
        token_secret: fake_token_secret
      })
    end
  end

  context "Validating tokens" do
    it "Should tell me when tokens are expired", :wip do
      url_to_mock = 'https://tripit.com/api/auth.test'
      request_opts = {
        headers: { 'Content-Type': 'application/json' },
        query: {
          token: 'fake-token'
        }
      }
      mocked_response_body = {
        ok: false,
        error: 'invalid_auth'
      }.to_json
      allow(HTTParty).to receive(:get)
        .with(url_to_mock, request_opts)
        .and_return(double(HTTParty::Response, body: mocked_response_body))
      expect(TripIt::Core::OAuth.token_expired?(token: 'fake-token')).to be true
    end

    it "Should tell me when tokens are not expired", :wip do
      url_to_mock = 'https://tripit.com/api/auth.test'
      request_opts = {
        headers: { 'Content-Type': 'application/json' },
        query: {
          token: 'fake-token'
        }
      }
      allow(HTTParty).to receive(:get)
        .with(url_to_mock, request_opts)
        .and_return(double(HTTParty::Response, body: { ok: true }.to_json))
      expect(TripIt::Core::OAuth.token_expired?(token: 'fake-token')).to be false
    end
  end
  context 'When making authenticated API calls' do
    it "Should yield correct authorization headers", :unit do
      oauth_consumer_key = 'fake-client-id'
      oauth_consumer_secret = 'fake-client-secret'
      oauth_token = 'fake-token'
      oauth_token_secret = 'fake-token-secret'
      oauth_nonce = 'fake-nonce'
      oauth_timestamp = '123'
      expected_signature = "68IrO5yjEP1faR5Q0Oj3Cplsxr8="
      uri = 'https://api.tripit.com/v1/foo'
      expected_auth_headers_hash = {
        oauth_consumer_key: oauth_consumer_key,
        oauth_nonce: oauth_nonce,
        oauth_timestamp: oauth_timestamp,
        oauth_signature_method: 'HMAC-SHA1',
        oauth_version: '1.0',
        oauth_token: oauth_token
      }
      expected_auth_headers = "OAuth realm=\"#{uri}\"," + \
        expected_auth_headers_hash.sort.to_h.map {|key, value| "#{key}=\"#{value}\""}.join(',')
      expected_auth_headers += ",oauth_signature=\"#{CGI.escape(expected_signature)}\""
      expect(TripIt::Core::OAuth::Authenticated.generate_headers(
        uri: uri,
        consumer_key: oauth_consumer_key,
        consumer_secret: oauth_consumer_secret,
        nonce: oauth_nonce,
        token: oauth_token,
        token_secret: oauth_token_secret,
        timestamp: oauth_timestamp))
        .to eq expected_auth_headers
    end
  end
end
