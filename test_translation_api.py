import requests
import json

try:
    # Test the API endpoint directly
    response = requests.get('http://localhost:5000/api/translations/en')
    if response.status_code == 200:
        data = response.json()
        print("API Response for recommendation keys:")
        print(f"recommendation_rank: {repr(data.get('recommendation_rank'))}")
        print(f"recommendation_suffix: {repr(data.get('recommendation_suffix'))}")
        print(f"click_to_contact: {repr(data.get('click_to_contact'))}")
        
        # Check if the suffix is actually empty
        suffix = data.get('recommendation_suffix')
        print(f"\nSuffix analysis:")
        print(f"Value: {repr(suffix)}")
        print(f"Type: {type(suffix)}")
        print(f"Is empty string: {suffix == ''}")
        print(f"Boolean evaluation: {bool(suffix)}")
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
