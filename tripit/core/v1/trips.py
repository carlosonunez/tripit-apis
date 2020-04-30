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
    return join_trips(trips_json['Trip'])


def join_trips(trips):
    """
    Since we need to make API calls to resolve flights in each trip,
    this function delegates these jobs into threads and joins them.
    """
    parsed_trip_futures = []
    for trip in trips:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            parsed_trip_futures.append(executor.submit(summarize_trip, trip))

    parsed_trips = [future.result() for future in parsed_trip_futures]
    return parsed_trips


def summarize_trip(trip_object):
    """
    Generates a summarized version of a trip with expanded flight
    information.
    """
    logger.debug("Fetching trip %s", trip_object['id'])
    return {
        'id': int(trip_object['id']),
        'name': trip_object['display_name'],
        'city': trip_object['primary_location'],
        'ends_on': resolve_end_time(trip_object),
        'ended': determine_if_trip_ended(trip_object),
        'link': "https://www.tripit.com" + trip_object['relative_url'],
        'starts_on': resolve_start_time(trip_object),
        'flights': []
    }


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
