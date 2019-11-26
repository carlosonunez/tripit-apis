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
        return TripIt::AWSHelpers::APIGateway.error(message: "Unable to find trips.")
      end
      all_trips = JSON.parse(all_trips_response.body,
                            symbolize_names: true)
      trips_in_form_that_we_care_about = []
      all_trips[:Trip].each do |trip|
        this_trip = self.summarize_trip_data(trip)
        trips_in_form_that_we_care_about.push this_trip
      end
      TripIt::AWSHelpers::APIGateway.ok(additional_json:{
        trips: trips_in_form_that_we_care_about
      })
    end

    private
    def self.summarize_trip_data(trip)
      this_trip = {}
      this_trip[:name] = trip[:display_name]
      this_trip[:city] = trip[:primary_location]
      this_trip[:ends_on] = Time.parse(trip[:end_date]).to_i
      this_trip[:link] = "https://www.tripit.com/#{trip[:relative_url]}"
      this_trip[:starts_on] = Time.parse(trip[:start_date]).to_i
      return this_trip
    end
  end
end
