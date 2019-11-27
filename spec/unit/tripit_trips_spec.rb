require 'spec_helper'
require 'yaml'

describe "Fetching trips" do
  context "When querying for trips" do
    it "Should return all trips with summarized information within them", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      expect(SecureRandom).to receive(:hex).exactly(4).times.and_return 'fake-nonce'
      expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
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
      ids = {
        personal: 123456789,
        no_flights: 293554303,
        has_flights: 293554133
      }
      expected_responses_from_tripit = {
        '/list/trip': 'sample_trips.json',
        "/get/trip/id/123456789/include_objects/true": 'sample_personal_trip.json',
        "/get/trip/id/293554303/include_objects/true": 'sample_trip_without_flights.json',
        "/get/trip/id/293554133/include_objects/true": 'sample_trip_with_flights.json'
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
      response = TripIt::Trips.get_all(fake_event)
      expect(response[:statusCode]).to eq 200
      response_body = JSON.parse(response[:body], symbolize_names: true)
      expect(response_body[:status]).to eq 'ok'
      actual_trips = response_body[:trips]
      expected_trips = YAML.load(File.read("spec/fixtures/expected_trip_info.yml"),
                                symbolize_names: true)

      ids.each do |trip_type, _|
        actual_trip = actual_trips.select{|trip| trip[:id] == ids[trip_type]}
        expected_trip = expected_trips.select{|trip| trip[:id] == ids[trip_type]}
        expect(actual_trip).not_to be_empty, "Failed on type: '#{trip_type}'"
        expect(actual_trip).to eq expected_trip
      end
    end
  end
end
