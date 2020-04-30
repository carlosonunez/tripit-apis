"""
TripIt operations.
"""
import concurrent.futures
import time
from tripit.core.v1.api import get_from_tripit_v1
from tripit.logging import logger


def get_all_trips(token, token_secret):
    """
    Retrieves all trips from TripIt and parses it in a way that's friendly to
    this API.

    We only care about flights and notes. Every other TripIt object is stripped out.
    """
    trip_data = get_from_tripit_v1(endpoint="/trips", token=token, token_secret=token_secret)
    logger.debug("Response: %d, Body: %s", trip_data.status_code, trip_data.json)
    if trip_data.status_code != 200:
        logger.error("Failed to get trips: %s", trip_data.status_code)
        return None
    trips_json = trip_data.json
    if "Trip" not in trips_json:
        logger.info("No trips found.")
        return []
    return join_trips(trips_json['Trip'], token, token_secret)


def join_trips(trips, token, token_secret):
    """
    Since we need to make API calls to resolve flights in each trip,
    this function delegates these jobs into threads and joins them.
    """
    parsed_trip_futures = []
    for trip in trips:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            parsed_trip_futures.append(executor.submit(summarize_trip, trip, token, token_secret))

    parsed_trips = [future.result() for future in parsed_trip_futures]
    return parsed_trips


def summarize_trip(trip_reference, token, token_secret):
    """
    Generates a summarized version of a trip with expanded flight
    information.

    This involves a nested API call and might be time-expensive!
    """
    logger.debug("Fetching trip %s", trip_reference['id'])
    trip_info = get_from_tripit_v1(endpoint=''.join(['/get/trip/id/', trip_reference['id']]),
                                   token=token,
                                   token_secret=token_secret)
    if trip_info.status_code != 200:
        logger.error("Unable to fetch trip %s, error %d", trip_reference['id'],
                     trip_info.status_code)
    trip_object = trip_info.json

    summarized_trip = {
        'id': int(trip_object['id']),
        'name': trip_object['display_name'],
        'city': trip_object['primary_location'],
        'ends_on': resolve_end_time(trip_object),
        'ended': determine_if_trip_ended(trip_object),
        'link': "https://www.tripit.com" + trip_object['relative_url'],
        'starts_on': resolve_start_time(trip_object),
        'flights': resolve_flights(trip_object)
    }
    return summarized_trip


def resolve_flights(trip_object):
    """
    Fetches flights for a given trip object, if any `AirObject`'s exist,
    sorted by their departure date and time.

    This involves a nested API call to the resource of the `Trip` and
    might be time-expensive!

    Note that a flight is a collection of segments, or "flight legs."
    """
    if not trip_object['AirObject']:
        logger.info("No air objects found for trip %s", trip_object['id'])
        return []

    # Fix bug from Ruby version wherein `AirObject`s aren't always
    # arrays.
    flights = normalize_air_objects_within_trip(trip_object)
    flight_segments = normalize_flight_segments_from_flights(flights)
    summarized_segments = []
    for segment in flight_segments:
        flight_number = ''.join(
            [segment['marketing_airline_code'], segment['marketing_flight_number']])
        summarized_segment = {
            'flight_number': flight_number,
            'origin': segment['start_airport_code'],
            'destination': segment['end_airport_code'],
            'offset': segment['StartDateTime']['utc_offset'],
            'depart_time': normalize_flight_time_to_tz(segment['StartDateTime']),
            'arrive_time': normalize_flight_time_to_tz(segment['EndDateTime'])
        }
        summarized_segments.append(summarized_segment)
    return sorted(summarized_segments, key=lambda segment: segment['depart_time'])


def normalize_flight_time_to_tz(time_object):
    """
    Returns the time of a flight with its offset accounted for.
    """
    datetime_str = ' '.join([time_object['date'], time_object['time']])
    offset_seconds = int(time_object['offset'].split(':')[0]) * 60
    datetime_unix = int(time.mktime(time.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")))
    return datetime_unix + offset_seconds


def normalize_air_objects_within_trip(trip):
    """
    This ensures that all `AirObjects` are in an array regardless of the amount
    found.
    """
    if not isinstance(trip['AirObject']):
        return [trip['AirObject']]
    return trip['AirObject']


def normalize_flight_segments_from_flights(flights):
    """
    Returns a list of segments for a given flight.
    This is in its own method because segments aren't always arrays, which means
    they need to be normalized first. I didn't want to muddy `resolve_flights`
    with this logic.
    """
    if not isinstance(segments, list):
        segments = [flights['Segment']]
    return flights['Segment']


def retrieve_trip_time_as_unix(time_to_retrieve):
    """
    Returns a trip's time in UNIX time format.
    """
    return int(time.mktime(time.strptime(time_to_retrieve, '%Y-%m-%d')))


def resolve_start_time(trip):
    """
    Resolves the correct start time for a trip based on its flights
    """

    # TODO: Actually implement this.
    return retrieve_trip_time_as_unix(trip['start_date'])


def resolve_end_time(trip):
    """
    Resolves the correct start time for a trip based on its flights
    or manual intervention from a note.
    """
    # TODO: Actually implement this.
    return retrieve_trip_time_as_unix(trip['end_date'])


# TODO: Remove this flake.
# pylint: disable=unused-argument
def determine_if_trip_ended(trip):
    """
    Uses flight data in the trip or manual notes to determine if a trip
    has actually ended.

    This is required because the end date of a trip does not contain any time
    data, and there are situations in which a trip can end past its original
    end date (i.e. redeye flights).
    """
    # TODO: Actually implement this.
    return False
