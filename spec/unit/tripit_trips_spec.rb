require 'spec_helper'
require 'yaml'

describe "Fetching trips" do
  context "When querying for trips" do
    it "Should return all trips with summarized information within them", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      expect(SecureRandom).to receive(:hex).and_return 'fake-nonce'
      expect(Time).to receive(:now).and_return(mocked_time)
      expect(TripIt::Auth).to receive(:get_tripit_token).and_return({
        body: { token: 'fake-token', token_secret: 'fake-token-secret' }.to_json
      })
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
        status: 200,
        body: {
          status: 'ok',
          trips: YAML.load(File.read("spec/fixtures/expected_trip_info.yml"))
        }.to_json
      }
      expected_responses_from_tripit = {
        '/list/trip': 'sample_trips.json',
        '/get/trip/293554303': 'sample_trip_without_flights.json',
        '/get/trip/293554133': 'sample_trip_with_flights.json'
      }
      expected_responses_from_tripit.each do |endpoint, fixture|
        uri = "https://api.tripit.com/v1#{endpoint}/format/json"
        mocked_response = double(HTTParty::Response, {
          code: 200,
          body: File.read("spec/fixtures/#{fixture}")
        })
        auth_header = Helpers::TripIt::OAuth::Authenticated.generate_test_headers(uri)
        expect(HTTParty).to receive(:get).with(uri, headers: {
          'Authorization': auth_header
        }).and_return(mocked_response)
      end
      expect(TripIt::Trips.get_all(fake_event)).to eq expected_response
    end
  end
end
