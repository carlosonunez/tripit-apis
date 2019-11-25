require 'spec_helper'

describe "Fetching trips" do
  context "When querying for trips" do
    it "Should return all trips" do
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
      expected_trips = [
        {
          name: 'trip-1',
          city: 'city',
          flights: [{
            number: 'aa1',
            origin: 'JFK',
            destination: 'LAX',
            estimated_departure_time: 123,
            estimated_arrival_time: 345
          },
          {
            number: 'aa2',
            origin: 'LAX',
            destination: 'JFK',
            estimated_departure_time: 123,
            estimated_arrival_time: 345
          }]
        }
      ]
      expected_response = {
        status: 200,
        body: {
          status: ok,
          trips: expected_trips
        }.to_json
      }
      expect(TripIt::Trips.get_all(fake_event)).to eq expected_response
    end
  end
end
