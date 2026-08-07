from geopy.geocoders import Nominatim
from geopy.distance import geodesic, great_circle
from app.world_distance import get_world_distance
def get_world_distance(location1: str, location2: str):
    """
    Calculates the straight-line (geodesic) distance between any two places in the world.
    """
    # Initialize Nominatim Geocoder with a unique user agent
    geolocator = Nominatim(user_agent="world_distance_calculator_2026")
    
    print(f"Searching coordinates for: '{location1}'...")
    loc1 = geolocator.geocode(location1)
    
    print(f"Searching coordinates for: '{location2}'...")
    loc2 = geolocator.geocode(location2)
    
    if not loc1 or not loc2:
        return "Error: One or both locations could not be found on the map."
    
    coords1 = (loc1.latitude, loc1.longitude)
    coords2 = (loc2.latitude, loc2.longitude)
    
    # Calculate distances
    # Geodesic uses the WGS-84 ellipsoid model (most accurate for Earth)
    km_distance = geodesic(coords1, coords2).kilometers
    miles_distance = geodesic(coords1, coords2).miles
    
    print("\n" + "="*40)
    print(f"📍 Origin: {loc1.address}")
    print(f"   Coordinates: {coords1}")
    print(f"🏁 Destination: {loc2.address}")
    print(f"   Coordinates: {coords2}")
    print("-"*40)
    print(f"📏 Distance: {km_distance:.2f} km ({miles_distance:.2f} miles)")
    print("="*40 + "\n")
    
    return km_distance

# --- Example Usage ---
if __name__ == "__main__":
    # You can pass any cities, towns, or villages worldwide!
    origin = input("Enter starting location (e.g., Tokyo, Japan or Kurnool, India): ")
    destination = input("Enter destination location (e.g., Paris, France or Hyderabad, India): ")
    
    get_world_distance(origin, destination)