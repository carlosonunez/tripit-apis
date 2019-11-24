require 'spec_helper'

describe "TripIt OAuth methods" do
  context 'Getting tokens' do
    it "Should get a token", :unit do
      url_to_mock = 'https://tripit.com/api/oauth.access'
      request_opts = {
        headers: { 'Content-Type': 'application/x-www-formencoded' },
        body: nil,
        query: {
          client_id: 'fake',
          client_secret: 'fake',
          code: 'fake',
          redirect_uri: 'fake'
        }
      }
      mocked_response_body = { access_token: 'fake-token' }.to_json
      allow(HTTParty).to receive(:post)
        .with(url_to_mock, request_opts)
        .and_return(double(HTTParty::Response, code: 200, body: mocked_response_body))
      response = TripItAPI::TripIt::OAuth.access(client_id: 'fake',
                                               client_secret: 'fake',
                                               code: 'fake',
                                               redirect_uri: 'fake')
      access_token = JSON.parse(response.body)['access_token']
      expect(access_token).to eq 'fake-token'
    end
  end

  context "Validating tokens" do
    it "Should tell me when tokens are expired", :unit do
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
      expect(TripItAPI::TripIt::OAuth.token_expired?(token: 'fake-token')).to be true
    end

    it "Should tell me when tokens are not expired", :unit do
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
      expect(TripItAPI::TripIt::OAuth.token_expired?(token: 'fake-token')).to be false
    end
  end
end
