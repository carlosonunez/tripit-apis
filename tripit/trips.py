"""
TripIt operations.
"""
import concurrent.futures
import datetime
import os
import time
from tripit.core.v1.api import get_from_tripit_v1
from tripit.logging import logger


def get_current_trip(token, token_secret):
    """
    Retrieves the trip that we're currently on, with flights, if any.

    Note that we only currently support being on one trip at a time and will
    only return the first trip found.

    There might be trips with multiple flights happening at the same time.
    This can happen if we're tracking someone else's flight on the same trip
    as the requestor's flight. Since it seems that names are not attached
    to AirObjects, we will need to use notes to manually exclude these flights.

    This fix may get added in a future release.
    """
    trips = get_all_trips(token, token_secret)
    now = int(datetime.datetime.now().timestamp())
    current_trip = [trip for trip in trips if trip["starts_on"] <= now <= trip["ends_on"]]
    if not current_trip:
        return {}
    first_current_trip = current_trip[0]
    current_flights = [
        flight
        for flight in first_current_trip["flights"]
        if flight["depart_time"] <= now <= flight["arrive_time"]
    ]
    if not current_flights:
        current_flight = {}
    else:
        current_flight = current_flights[0]
    return {
        "trip_name": first_current_trip["name"],
        "current_city": first_current_trip["city"],
        "todays_flight": current_flight,
    }


def get_all_trips(token, token_secret, human_times=False):
    """
    Retrieves all trips from TripIt and parses it in a way that's friendly to
    this API.

    We only care about flights and notes. Every other TripIt object is stripped out.
    """
    trip_data = get_from_tripit_v1(endpoint="/list/trip", token=token, token_secret=token_secret,
                                   params={"include_objects": "true"})
    logger.debug("Response: %d, Text: %s", trip_data.status_code, trip_data.text)
    if trip_data.status_code != 200:
        logger.error("Failed to get trips: %s", trip_data.status_code)
        return None
    trips_json = trip_data.json()
    if "Trip" not in trips_json:
        logger.info("No trips found.")
        return []
    return join_trips(normalize_trip_objects(trips_json["Trip"]),
                      flights=trips_json.get("AirObject", []),
                      notes=trips_json.get("NoteObject", []),
                      token=token,
                      token_secret=token_secret,
                      human_times=human_times)


def join_trips(trips, flights, notes, token, token_secret, human_times):
    """
    Since we need to make API calls to resolve flights in each trip,
    this function delegates these jobs into threads and joins them.
    """
    parsed_trip_futures = []
    for trip_obj in trips:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            parsed_trip_futures.append(
                    executor.submit(resolve_trip, trip_obj, flights, notes, token,
                                    token_secret, human_times)
                    )

    parsed_trips = [future.result() for future in parsed_trip_futures]
    return [trip for trip in parsed_trips if trip]


def resolve_trip(trip_object, flights, notes, token, token_secret, human_times):
    """
    Generates a summarized version of a trip with expanded flight
    information.
    """
    logger.debug("Fetching trip %s", trip_object["id"])
    if trip_is_empty(trip_object):
        logger.warn("Trip %s is empty", trip_object["id"])
        return {}
    
    flight_objects = [ obj
                      for obj in flights
                      if obj["trip_id"] == trip_object["id"]
                     ]
    if len(flight_objects) == 0:
        logger.warn("Trip %s has no flight objects", trip_object["id"])
    note_objects = [ obj
                      for obj in notes
                      if obj["trip_id"] == trip_object["id"]
                   ]
    if len(note_objects) == 0:
        logger.warn("Trip %s has no notes attached to it", trip_object["id"])
    flights = resolve_flights(flight_objects, human_times)
    trip_start_time = resolve_start_time(trip_object, flights, human_times)
    trip_end_time = resolve_end_time(trip_object, flights, human_times)
    primary_location = resolve_primary_location(trip_object)

    summarized_trip = {
        "id": int(trip_object["id"]),
        "name": trip_object["display_name"],
        "city": primary_location,
        "ends_on": trip_end_time,
        "ended": determine_if_trip_ended(trip_end_time, note_objects),
        "link": "https://www.tripit.com" + trip_object["relative_url"],
        "starts_on": trip_start_time,
        "flights": flights,
    }
    if human_times:
        for key in ["starts_on", "ends_on"]:
            summarized_trip[key] = convert_to_human_dt(summarized_trip[key])
    return summarized_trip


def resolve_flights(trip_object, human_times):
    """
    Fetches flights for a given trip object, if any `AirObject`'s exist,
    sorted by their departure date and time.

    This involves a nested API call to the resource of the `Trip` and
    might be time-expensive!

    Note that a flight is a collection of segments, or "flight legs."
    """
    if not trip_object:
        return []

    # Fix bug from Ruby version wherein `AirObject`s aren't always
    # arrays.
    air_objects = normalize_air_objects_within_trip(trip_object)
    flights = normalize_flights_from_air_objects(air_objects)
    summarized_segments = []
    for flight in flights:
        segments = normalize_segments_from_flight(flight)
        for segment in segments:
            flight_number = "".join(
                [segment["marketing_airline_code"], segment["marketing_flight_number"]]
            )
            summarized_segment = {
                "flight_number": flight_number,
                "origin": segment["start_airport_code"],
                "destination": segment["end_airport_code"],
                "offset": segment["StartDateTime"]["utc_offset"],
                "depart_time": normalize_flight_time_to_tz(segment["StartDateTime"]),
                "arrive_time": normalize_flight_time_to_tz(segment["EndDateTime"]),
            }
            if human_times:
                for key in ["depart_time", "arrive_time"]:
                    summarized_segment[key] = convert_to_human_dt(summarized_segment[key])

            summarized_segments.append(summarized_segment)
    return sorted(summarized_segments, key=lambda segment: segment["depart_time"])


def convert_to_human_dt(timestamp):
    """
    Converts a timestamp to human time.
    """
    return datetime.datetime.utcfromtimestamp(timestamp).strftime("%a %b %d %H:%M:%S %Y %z UTC")


def convert_human_dt_to_ts(date_str):
    """
    Converts a human time to a timestamp.
    """
    return int(datetime.datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y UTC").timestamp())


def normalize_segments_from_flight(flight):
    """
    Same as the other normalization methods, but for segments.
    """
    segment = flight["Segment"]
    if isinstance(segment, list):
        return segment
    return [segment]


def resolve_start_time(trip, flights, human_times):
    """
    Resolves the correct start time for a trip based on its flights.

    Note that this assumes that our trips start with flights. That isn't always the case.
    This will need to be refactored once we start taking other trip objects into account.
    """
    if not flights:
        logger.debug("Trip: %s", str(trip))
        if "start_date" not in trip.keys():
            logger.warn("Trip %s doesn't have a start time!", trip["id"])
        return retrieve_trip_time_as_unix(trip.get("start_date", "1970-01-01"))

    first_flight_segment_start_time = flights[0]["depart_time"]
    if human_times:
        first_flight_segment_start_time = convert_human_dt_to_ts(first_flight_segment_start_time)

    if os.getenv("TRIPIT_INGRESS_TIME_MINUTES"):
        trip_ingress_seconds = int(os.getenv("TRIPIT_INGRESS_TIME_MINUTES")) * 60
    else:
        trip_ingress_seconds = 0

    return first_flight_segment_start_time + trip_ingress_seconds


def resolve_primary_location(trip):
    """
    Retrieves the primary location of this trip, if one is present.
    """
    if "primary_location" not in trip.keys():
        logger.warn("Trip %s does not have a primary location! Object: %s", trip["id"], str(trip))
        return "Anywhere, Earth"
    return trip["primary_location"]


def resolve_end_time(trip, flights, human_times):
    """
    Resolves the correct start time for a trip based on its flights
    or manual intervention from a note.

    Note that this assumes that our trips end with flights. That isn't always the case.
    This will need to be refactored once we start taking other trip objects into account.
    """
    if "end_date" not in trip:
        logger.warn("Trip %s doesn't have an end date!", trip["id"])
    trip_end_time = retrieve_trip_time_as_unix(trip.get("end_date", "1970-01-01"))
    if not flights:
        return trip_end_time

    last_flight_segment_end_time = flights[-1]["arrive_time"]
    if human_times:
        last_flight_segment_end_time = convert_human_dt_to_ts(last_flight_segment_end_time)

    if trip_end_time > last_flight_segment_end_time:
        return trip_end_time
    return last_flight_segment_end_time


def normalize_flight_time_to_tz(time_object):
    """
    Returns the time of a flight with its offset accounted for.
    """
    datetime_str = " ".join(
        [time_object["date"], time_object["time"], time_object["utc_offset"].replace(":", "")]
    )
    datetime_unix = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S %z").timestamp()
    return int(datetime_unix)


def normalize_trip_objects(trip):
    """
    This ensure that all trips are in an array.
    """
    if not isinstance(trip, list):
        return [trip]
    return trip


def normalize_air_objects_within_trip(trip):
    """
    This ensures that all `AirObjects` are in an array regardless of the amount
    found.
    """
    if not isinstance(trip, list):
        return [trip]
    return trip


def normalize_flights_from_air_objects(flights):
    """
    Returns a list of segments for a given flight.
    This is in its own method because segments aren't always arrays, which means
    they need to be normalized first. I didn't want to muddy `resolve_flights`
    with this logic.
    """
    if not isinstance(flights, list):
        return [flights]
    return flights


def retrieve_trip_time_as_unix(time_to_retrieve):
    """
    Returns a trip's time in UNIX time format.
    """
    return int(time.mktime(time.strptime(time_to_retrieve, "%Y-%m-%d")))


def trip_is_empty(trip):
    """
    Determines if a trip is empty.
    """
    required_keys = ["primary_location", "start_date", "end_date"]
    missing_keys = [key for key in required_keys if key in trip.keys()]
    return len(missing_keys) == 0


def determine_if_trip_ended(trip_end_time, note_objects):
    """
    Uses flight data in the trip or manual notes to determine if a trip
    has actually ended.

    This is required because the end date of a trip does not contain any time
    data, and there are situations in which a trip can end past its original
    end date (i.e. redeye flights).
    """
    trip_ended_notes = [note for note in note_objects if note["display_name"] == "TRIP_ENDED"]
    if trip_ended_notes:
        return True
    current_time = int(datetime.datetime.now().timestamp())
    return current_time > trip_end_time
