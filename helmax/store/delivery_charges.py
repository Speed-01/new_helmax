import requests

# Enhanced delivery charges with more granular pricing
delivery_charges = {
  # Metro Cities (Tier 1) - Rs.50
  'mumbai': 50,
  'delhi': 50,
  'bangalore': 50,
  'kolkata': 50,
  'chennai': 50,
  'hyderabad': 50,
  'new delhi': 50,

  # Tier 2 Cities - Rs.70
  'pune': 70,
  'ahmedabad': 70,
  'surat': 70,
  'lucknow': 70,
  'jaipur': 70,
  'kochi': 70,
  'coimbatore': 70,
  'indore': 70,
  'nagpur': 70,
  'bhopal': 70,
  'visakhapatnam': 70,
  'vadodara': 70,
  'thiruvananthapuram': 70,
  'gurugram': 70,
  'noida': 70,
  'kaniyapuram': 20,

  # States - for fallback when city isn't in database
  'kerala': 80,
  'maharashtra': 80,
  'tamil nadu': 80,
  'karnataka': 75,
  'telangana': 75,
  'andhra pradesh': 85,
  'uttar pradesh': 85,
  'gujarat': 80,
  'west bengal': 85,
  'rajasthan': 90,
  'madhya pradesh': 90,
  'bihar': 95,
  'odisha': 95,
  'assam': 100,
  'punjab': 85,
  'haryana': 80,
  'jharkhand': 95,
  'chhattisgarh': 95,
}

# Distance-based pricing tiers
distance_pricing = {
  'local': {'base': 30, 'per_km': 5, 'max_distance': 5},
  'city': {'base': 50, 'per_km': 8, 'max_distance': 15},
  'regional': {'base': 80, 'per_km': 10, 'max_distance': 50},
  'national': {'base': 120, 'per_km': 15, 'max_distance': float('inf')}
}

# Free shipping threshold
FREE_SHIPPING_THRESHOLD = 1000

# Default charge if location not found
DEFAULT_CHARGE = 100

def reverse_geocode(latitude, longitude):
    """Convert coordinates to location information."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
        headers = {
            'User-Agent': 'HelMax E-commerce Application'
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Extract location details
        address = data.get('address', {})
        city = address.get('city', '').lower()
        state = address.get('state', '').lower()
        country = address.get('country', '').lower()
        
        return {
            'city': city,
            'state': state,
            'country': country,
            'full_address': data.get('display_name', '')
        }
    except Exception as e:
        print(f"Geocoding error: {e}")
        return {'city': '', 'state': '', 'country': '', 'full_address': ''}

def get_delivery_charge(location, order_amount=0):
    """Calculate delivery charge based on location."""
    # Free shipping for orders above threshold
    if order_amount >= FREE_SHIPPING_THRESHOLD:
        return 0
    
    city = location.get('city', '').lower()
    state = location.get('state', '').lower()
    
    # Check if city is in our database
    if city in delivery_charges:
        return delivery_charges[city]
    
    # Fall back to state-based pricing
    if state in delivery_charges:
        return delivery_charges[state]
    
    # Default charge if location not recognized
    return DEFAULT_CHARGE

def calculate_distance_based_charge(distance_km, order_amount=0):
    """Calculate delivery charge based on distance."""
    # Free shipping for orders above threshold
    if order_amount >= FREE_SHIPPING_THRESHOLD:
        return 0
    
    # Determine pricing tier based on distance
    if distance_km <= distance_pricing['local']['max_distance']:
        tier = 'local'
    elif distance_km <= distance_pricing['city']['max_distance']:
        tier = 'city'
    elif distance_km <= distance_pricing['regional']['max_distance']:
        tier = 'regional'
    else:
        tier = 'national'
    
    # Calculate charge: base + per_km rate for distance beyond base
    pricing = distance_pricing[tier]
    charge = pricing['base'] + pricing['per_km'] * distance_km
    
    return round(charge)