require 'spec_helper'

describe "Getting trip information" do
  context "When visiting /trips" do
    it "Should give me trips", :integration do
      uri = "#{$api_gateway_url}/trips"
      response = HTTParty.get(uri, {
        headers: { 'x-api-key': $test_api_key }
      })
      expected_response = File.read('spec/fixtures/integration/expected_response.json')
      actual_response = response.body
      expect(response.code.to_i).to eq 200

      expected_trips = JSON.parse(expected_response, symbolize_names: true)[:trips]
      actual_trips = JSON.parse(actual_response, symbolize_names: true)[:trips]
      ids = {
        personal: 293554288, 
        no_flights: 293554303,
        has_flights: 293554133
      }
      ids.each do |trip_type, _|
        actual_trip = actual_trips.select{|trip| trip[:id] == ids[trip_type]}
        expected_trip = expected_trips.select{|trip| trip[:id] == ids[trip_type]}
        expect(actual_trip).not_to be_empty, "Failed on type: '#{trip_type}'"
        expect(actual_trip).to eq expected_trip
      end
    end
  end

  context "When visiting /current_trip" do
    # Integration testing these will be difficult since their results are
    # time-dependent and we can't mock the time within Lambda.
    # While our unit tests cover most of the expected behavior, it would be good
    # to see how these functions behave against a real DynamoDB instance and within
    # Lambda.
    #
    # Thus, I will leave the shells of these tests as :wip and complete
    # them when I have more time to do so. Note that there might be instability
    # with these functions because of this.
    it "Should give me today's trip", :wip do
    end

    it "Should give me today's trip and today's flight, if any", :wip do
    end
  end
end
