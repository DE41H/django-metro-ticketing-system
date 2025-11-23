from stations.utils import calculate_route
from stations.models import Station

def calculate_ticket_price(start: Station, stop: Station) -> float:
    return len(calculate_route(start, stop)) * 10.0
