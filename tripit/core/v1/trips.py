"""
TripIt operations.
"""
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
    trips = trip_data.json
    if "Trip" not in trips:
        logger.info("No trips found.")
        return []
    return trips
