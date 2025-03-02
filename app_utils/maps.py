from geopy.geocoders import Nominatim
import requests
import traceback
# Function to convert address to latitude/longitude using geopy
from functools import lru_cache

@lru_cache(maxsize=100)
def get_location(address):
    geolocator = Nominatim(user_agent="streamlit_route_app", timeout=10)
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    return None

# Function to get the route details (polyline, distance, duration) using OSRM API
def get_route(source_coords, dest_coords):
    # OSRM expects coordinates as lon,lat
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{source_coords[1]},{source_coords[0]};{dest_coords[1]},{dest_coords[0]}"
        f"?overview=full&geometries=geojson"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get route. Status code: {response.status_code}")
    data = response.json()
    route_coords = data['routes'][0]['geometry']['coordinates']
    distance = data['routes'][0]['distance']   # in meters
    duration = data['routes'][0]['duration']   # in seconds
    # Convert coordinates back to (lat, lon) pairs for folium
    route_latlon = [(coord[1], coord[0]) for coord in route_coords]
    return route_latlon, distance, duration


def calculate_maps_data(destination: str):
    map_data = {}
    source = "Kolkata"
    print("destination", destination)
    try:
        source_coords = get_location(source)
        dest_coords = get_location(destination)
        
        if source_coords and dest_coords:
            # Store coordinates in session state
            map_data['source_coords'] = source_coords
            map_data['dest_coords'] = dest_coords
            
            # Get and store route details
            route, distance, duration = get_route(source_coords, dest_coords)
            map_data['route'] = route
            map_data['distance'] = distance
            map_data['duration'] = duration
            return map_data
        else:
            raise Exception("Could not find one or both of the locations. Please try different inputs.")
    except Exception as e:
        traceback.print_exc()
        raise e