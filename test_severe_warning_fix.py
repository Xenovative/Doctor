#!/usr/bin/env python3
"""
Test script to reproduce the severe warning 400 error
"""
import requests
import json

def test_find_doctor_endpoint():
    """Test the /find_doctor endpoint with typical formData"""
    
    # Simulate the formData that would be sent from the severe warning system
    test_data = {
        "age": 35,
        "gender": "男",
        "symptoms": "胸痛、呼吸困難、頭暈",
        "chronicConditions": "高血壓、糖尿病",
        "language": "中文",
        "location": "香港島",
        "locationDetails": {
            "region": "香港島",
            "district": "中西區", 
            "area": "中環"
        },
        "detailedHealthInfo": {
            "height": "175",
            "weight": "70",
            "medications": "降血壓藥",
            "allergies": "",
            "surgeries": "",
            "bloodThinner": False,
            "recentVisit": False,
            "cpapMachine": False,
            "looseTeeth": False
        },
        "uiLanguage": "zh-TW"
    }
    
    print("Testing /find_doctor endpoint...")
    print("Sending data:", json.dumps(test_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            'http://localhost:7001/find_doctor',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! Response:", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"ERROR {response.status_code}:")
            print("Raw response text:", response.text)
            try:
                error_data = response.json()
                print("Parsed error:", json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print("Could not parse error response as JSON")
                
    except Exception as e:
        print(f"Request failed: {e}")

def test_with_missing_fields():
    """Test with missing required fields to see validation errors"""
    
    test_cases = [
        {"name": "Missing age", "data": {"symptoms": "胸痛", "language": "中文", "location": "香港島"}},
        {"name": "Missing symptoms", "data": {"age": 35, "language": "中文", "location": "香港島"}},
        {"name": "Missing language", "data": {"age": 35, "symptoms": "胸痛", "location": "香港島"}},
        {"name": "Missing location", "data": {"age": 35, "symptoms": "胸痛", "language": "中文"}},
        {"name": "Invalid age", "data": {"age": "invalid", "symptoms": "胸痛", "language": "中文", "location": "香港島"}},
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        try:
            response = requests.post(
                'http://localhost:7001/find_doctor',
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    print("=== Testing Find Doctor Endpoint ===")
    test_find_doctor_endpoint()
    
    print("\n=== Testing Validation Errors ===")
    test_with_missing_fields()
