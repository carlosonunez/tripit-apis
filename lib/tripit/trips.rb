require 'thread'
require 'tripit/aws_helpers/api_gateway'

module TripIt
  module Trips
    def self.get_all(event)
      token_data = JSON.parse(TripIt::Auth.get_tripit_token(event: event)[:body],
                              symbolize_names: true)
      token = token_data[:token]
      token_secret = token_data[:token_secret]
      all_trips_response = TripIt::Core::API::V1.get_from(endpoint: '/list/trip',
                                                          token: token,
                                                          token_secret: token_secret)
      if all_trips_response.code != 200
        return TripIt::AWSHelpers::APIGateway.error(
          message: "Unable to find trips: #{all_trips_response.body}"
        )
      end
      all_trips = JSON.parse(all_trips_response.body,
                            symbolize_names: true)
      trip_threads = []
      summarized_trips = []
      all_trips[:Trip].each do |trip|
        parameters = {trip: trip, token: token, token_secret: token_secret}
        trip_threads << Thread.new(parameters) do |parameters_in_thread|
          trip_id = parameters_in_thread[:trip][:id].to_i
          summarized_trip = self.summarize_trip_data(parameters_in_thread[:trip],
                                                     parameters_in_thread[:token],
                                                     parameters_in_thread[:token_secret])
          summarized_trip[:flights] = self.get_flight_data(trip_id,
                                                          token,
                                                          token_secret)
          summarized_trips << summarized_trip
        end
      end
      trip_threads.each(&:join)

      TripIt::AWSHelpers::APIGateway.ok(additional_json:{
        trips: summarized_trips
      })
    end

    def self.get_current_trip(event)
      all_trips_response = self.get_all(event)
      if all_trips_response[:statusCode] != 200
        return TripIt::AWSHelpers::APIGateway.error(
          message: "Unable to fetch trips: #{all_trips[:body]}"
        )
      end
      all_trips = JSON.parse(all_trips_response[:body],
                             symbolize_names: true)
      summarized_current_trip = {}
      current_time = Time.now.to_i
      current_trip =
        all_trips.select {|trip|
          current_time >= trip[:starts_on] && current_time < trip[:ends_on]
        }
        .sort {|trip| trip[:starts_on]}
        .first
      summarized_current_trip[:trip_name] = current_trip[:name]
      summarized_current_trip[:todays_flight] = {}
      current_date = Time.now.strftime("%Y-%m-%d")
      if !current_trip[:flights].empty?
        current_flight = current_trip[:flights]
          .select{|flight|
            departure_date = Time.at(flight[:depart_time]).strftime("%Y-%m-%d")
            current_date == departure_date
          }
          .first || {}
        summarized_current_trip[:todays_flight] = current_flight
      end
      summarized_current_trip
    end

    private
    def self.summarize_trip_data(trip, token, token_secret)
      this_trip = {}
      this_trip[:id] = trip[:id].to_i
      this_trip[:name] = trip[:display_name]
      this_trip[:city] = trip[:primary_location]
      this_trip[:ends_on] = Time.parse(trip[:end_date]).to_i
      this_trip[:link] = "https://www.tripit.com#{trip[:relative_url]}"
      this_trip[:starts_on] = Time.parse(trip[:start_date]).to_i
      this_trip
    end

    def self.get_flight_data(trip_id, token, token_secret)
      response = TripIt::Core::API::V1.get_from(
        endpoint: "get/trip/id/#{trip_id}",
        params: {
          include_objects: true
        },
        token: token,
        token_secret: token_secret
      )
      if response.code != 200
        puts "WARN: Unable to get data for ID #{trip_id}: #{response.body}"
      end
      trip_data = JSON.parse(response.body, symbolize_names: true)
      if !trip_data.key?(:AirObject)
        []
      else
        flight_data = trip_data[:AirObject]
        summarized_flight_data = []
        flight_data[:Segment].each do |flight_leg|
          summarized_flight = {}
          summarized_flight[:flight_number] = [
            flight_leg[:marketing_airline_code],
            flight_leg[:marketing_flight_number]
          ].join
          summarized_flight[:origin] = flight_leg[:start_airport_code]
          summarized_flight[:destination] = flight_leg[:end_airport_code]
          summarized_flight[:depart_time] = Time.parse([
            flight_leg[:StartDateTime][:date],
            flight_leg[:StartDateTime][:time],
            flight_leg[:StartDateTime][:utc_offset]
          ].join(' ')).to_i
          summarized_flight[:arrive_time] = Time.parse([
            flight_leg[:EndDateTime][:date],
            flight_leg[:EndDateTime][:time],
            flight_leg[:EndDateTime][:utc_offset]
          ].join(' ')).to_i
          summarized_flight_data << summarized_flight
        end
        summarized_flight_data
      end
    end
  end
end