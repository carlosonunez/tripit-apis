"""
TripIt operations.
"""
from tripit.core.v1.api import get_from_tripit_v1

def get_all_trips():
    """
    Retrieves all trips from TripIt and parses it in a way that's friendly to
    this API.

    We only care about flights and notes. Every other TripIt object is stripped out.
    """
    
