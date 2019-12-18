require 'spec_helper'
require 'yaml'

describe "Fetching trips" do
  context "When querying for trips" do
    it "Should return all trips with summarized information within them", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
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
        has_flights: 293554134,
        single_segment: 234567890,
      }
      expected_responses_from_tripit = {
        '/list/trip': 'sample_trips.json',
        "/get/trip/id/123456789/include_objects/true": 'sample_personal_trip.json',
        "/get/trip/id/293554303/include_objects/true": 'sample_trip_without_flights.json',
        "/get/trip/id/293554134/include_objects/true": 'sample_trip_with_flights.json',
        "/get/trip/id/234567890/include_objects/true": 'sample_trip_single_segment.json',
        "/get/trip/id/345678901/include_objects/true": 'sample_trip_that_ended.json'
      }
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
      expect(SecureRandom).to receive(:hex)
        .exactly(expected_responses_from_tripit.count).times
        .and_return 'fake-nonce'
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

    it "Should return trips with friendly datetimes", :unit do
      ENV['TRIPIT_APP_CLIENT_ID'] = 'fake-client-id'
      ENV['TRIPIT_APP_CLIENT_SECRET'] = 'fake-client-secret'
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
        },
        queryStringParameters: {
          human_times: 'true'
        }
      }.to_json)
      ids = {
        personal: 123456789,
        no_flights: 293554303,
        has_flights: 293554134,
        single_segment: 234567890,
      }
      expected_responses_from_tripit = {
        '/list/trip': 'sample_trips.json',
        "/get/trip/id/123456789/include_objects/true": 'sample_personal_trip.json',
        "/get/trip/id/293554303/include_objects/true": 'sample_trip_without_flights.json',
        "/get/trip/id/293554134/include_objects/true": 'sample_trip_with_flights.json',
        "/get/trip/id/234567890/include_objects/true": 'sample_trip_single_segment.json',
        "/get/trip/id/345678901/include_objects/true": 'sample_trip_single_segment.json'
      }
      mocked_time = Time.parse("1969-12-31 18:02:03 -0600") # 123
      expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
      expect(SecureRandom).to receive(:hex)
        .exactly(expected_responses_from_tripit.count).times
        .and_return 'fake-nonce'
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
      expected_trips =
        YAML.load(File.read("spec/fixtures/expected_trip_info_friendly_times.yml"),
                  symbolize_names: true)

      ids.each do |trip_type, _|
        actual_trip = actual_trips.select{|trip| trip[:id] == ids[trip_type]}
        expected_trip = expected_trips.select{|trip| trip[:id] == ids[trip_type]}
        expect(actual_trip).not_to be_empty, "Failed on type: '#{trip_type}'"
        expect(actual_trip).to eq expected_trip
      end
    end
  end

  context "When getting the next event" do
    it "Should only return the trip name if we are not en route to some place", :unit do
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
      sample_trips = YAML.load(File.read('spec/fixtures/expected_trip_info.yml'),
                               symbolize_names: true)
      sample_trips_without_matching_flight =
        sample_trips.each{|trip|
          trip[:flights] = trip[:flights].reject{|flight|
            flight[:flight_number] == 'AA356'
          }}
      expect(TripIt::Trips).to receive(:get_all)
        .with(fake_event)
        .and_return({
        statusCode: 200,
        body: {
          status: 'ok',
          trips: sample_trips_without_matching_flight
        }.to_json
      })
      expected_trip = {
        statusCode: 200,
        body: {
          status: 'ok',
          trip: {
            trip_name: 'Work: Test Client - Week 3',
            current_city: 'Omaha, NE',
            todays_flight: {}
          }
        }.to_json
      }
      mocked_time = Time.parse('2019-12-01')
      expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
      active_trip = TripIt::Trips.get_current_trip(fake_event)
      expect(active_trip).to eq expected_trip
    end
    it "Should return the trip and any active flights associated with it that day", :unit do
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
        expect(TripIt::Trips).to receive(:get_all)
          .with(fake_event)
          .and_return({
          statusCode: 200,
          body: {
            status: 'ok',
            trips: YAML.load(File.read('spec/fixtures/expected_trip_info.yml'))
          }.to_json
        })
        expected_trip = {
          statusCode: 200,
          body: {
            status: 'ok',
            trip: {
              trip_name: 'Work: Test Client - Week 2',
              current_city: 'Omaha, NE',
              todays_flight: {
                flight_number: "AA356",
                origin: "DFW",
                destination: "OMA",
                depart_time: 1575241860,
                arrive_time: 1575248160,
                offset: "-06:00"
              }
            }
          }.to_json
        }
        mocked_time = Time.at(1575243000)
        expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
        active_trip = TripIt::Trips.get_current_trip(fake_event)
        expect(active_trip).to eq expected_trip
    end
    it "Should return no trips if no active trips are found", :unit do
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
        expect(TripIt::Trips).to receive(:get_all)
          .with(fake_event)
          .and_return({
          statusCode: 200,
          body: {
            status: 'ok',
            trips: YAML.load(File.read('spec/fixtures/expected_trip_info.yml'))
          }.to_json
        })
        expected_trip = {
          statusCode: 200,
          body: {
            status: 'ok',
            trip: {}
          }.to_json
        }
        mocked_time = Time.at(2000000000)
        expect(Time).to receive(:now).at_least(1).times.and_return(mocked_time)
        active_trip = TripIt::Trips.get_current_trip(fake_event)
        expect(active_trip).to eq expected_trip
    end
  end
end
