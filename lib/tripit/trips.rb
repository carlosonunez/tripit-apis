require 'thread'
require 'tripit/aws_helpers/api_gateway'

module TripIt
  module Trips
    def self.get_all(event)
      token_data = JSON.parse(TripIt::Auth.get_tripit_token(event: event)[:body],
                              symbolize_names: true)
      friendly_times = event.dig('queryStringParameters',
                                 'human_times') == 'true'
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
          summarized_trip =
            self.summarize_trip_data(parameters_in_thread[:trip],
                                     parameters_in_thread[:token],
                                     parameters_in_thread[:token_secret],
                                     human_times: friendly_times)
          summarized_trip[:flights] =
            self.get_flight_data(trip_id,
                                 token,
                                 token_secret,
                                 human_times: friendly_times)
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
                             symbolize_names: true)[:trips]
      current_time = Time.now.to_i

      # TripIt uses +%F format for their start and end dates. This causes
      # us to not find any trips when our current date matches the end date
      # at the top of the hour.
      #
      # Fix this by adding a 23h59m offset.
      offset_to_end_of_day_seconds = 86340
      current_trip =
        all_trips.select do |trip|
          current_time >= trip[:starts_on] &&
            current_time < (trip[:ends_on] + offset_to_end_of_day_seconds)
        end
          .sort{|first, second| first[:id] <=> second[:id]}
          .last
      if current_trip.nil?
        return TripIt::AWSHelpers::APIGateway.ok(additional_json: { trip: {} })
      end
      summarized_current_trip = {}
      summarized_current_trip[:trip_name] = current_trip[:name]
      summarized_current_trip[:current_city] = current_trip[:city] || 'No city'
      summarized_current_trip[:todays_flight] = {}
      if !current_trip[:flights].empty?
        current_flight = current_trip[:flights]
          .select{|flight|
            true_offset = flight[:offset].to_i + Time.now.strftime("%:z").to_i
            adjusted_current_time =
              Time.at(current_time).getlocal(flight[:offset].to_i + true_offset).to_i
            origin_egress_seconds =
              (ENV['TRIPIT_DEFAULT_ORIGIN_EGRESS_HOURS'].to_i*3600) || 5400
            destination_ingress_seconds =
              (ENV['TRIPIT_DEFAULT_DESTINATION_INGRESS_HOURS'].to_i*3600) || 5400
            departure_time = flight[:depart_time]
            arrive_time = flight[:arrive_time]
            adjusted_current_time >= (departure_time-origin_egress_seconds) &&
              adjusted_current_time < (arrive_time+destination_ingress_seconds)
          }
          .first || {}
        summarized_current_trip[:todays_flight] = current_flight
      end
      TripIt::AWSHelpers::APIGateway.ok(additional_json: {
        trip: summarized_current_trip
      })
    end

    private
    def self.summarize_trip_data(trip, token, token_secret, human_times: false)
      this_trip = {}
      this_trip[:id] = trip[:id].to_i
      this_trip[:name] = trip[:display_name]
      this_trip[:city] = trip[:primary_location]
      this_trip[:ends_on] = Time.parse(trip[:end_date]).to_i
      this_trip[:link] = "https://www.tripit.com#{trip[:relative_url]}"
      this_trip[:starts_on] = Time.parse(trip[:start_date]).to_i

      if human_times
        %i[ends_on starts_on].each do |key|
          this_trip[key] = Time.at(this_trip[key].to_i).strftime("%c %Z")
        end
      end
      this_trip
    end

    def self.get_flight_data(trip_id, token, token_secret, human_times: false)
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
        # This data doesn't always return an Array. I'm not sure if
        # this is an issue with the JSON library or with TripIt's schema.
        if flight_data.is_a? Hash
          flight_data = [flight_data]
        end
        flight_data.each do |flight_data_object|
          flight_legs = [flight_data_object[:Segment]].flatten
          flight_legs.each do |flight_leg|
            summarized_flight = {}
            summarized_flight[:flight_number] = [
              flight_leg[:marketing_airline_code],
              flight_leg[:marketing_flight_number]
            ].join
            summarized_flight[:origin] = flight_leg[:start_airport_code]
            summarized_flight[:destination] = flight_leg[:end_airport_code]
            summarized_flight[:offset] = flight_leg[:StartDateTime][:utc_offset]
            summarized_flight[:depart_time] = Time.parse([
              flight_leg[:StartDateTime][:date], flight_leg[:StartDateTime][:time],
              flight_leg[:StartDateTime][:utc_offset]
            ].join(' ')).to_i
            summarized_flight[:arrive_time] = Time.parse([
              flight_leg[:EndDateTime][:date],
              flight_leg[:EndDateTime][:time],
              flight_leg[:EndDateTime][:utc_offset]
            ].join(' ')).to_i

            if human_times
              %i[depart_time arrive_time].each do |key|
                summarized_flight[key] =
                  Time.at(summarized_flight[key].to_i).strftime("%c %Z")
              end
            end
            summarized_flight_data << summarized_flight
          end
        end
        summarized_flight_data
      end
    end
  end
end
