#!/usr/bin/env python3
"""
Debug script to test emergency tag detection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import diagnose_symptoms, check_emergency_needed

def test_emergency_symptoms():
    """Test with symptoms that should trigger emergency"""
    
    print("=== Testing Emergency Symptoms ===")
    
    # Test case 1: Clear emergency symptoms
    test_symptoms = "胸痛、呼吸困難、心跳很快、冒冷汗"
    chronic_conditions = "高血壓、糖尿病"
    
    print(f"Testing symptoms: {test_symptoms}")
    print(f"Chronic conditions: {chronic_conditions}")
    
    # Call the diagnosis function
    result = diagnose_symptoms(35, "男", test_symptoms, chronic_conditions, {}, 'zh-TW')
    
    print(f"\nAI Diagnosis Response:")
    print("=" * 50)
    print(result['diagnosis'])
    print("=" * 50)
    
    print(f"\nExtracted Results:")
    print(f"- Recommended Specialty: {result['recommended_specialty']}")
    print(f"- Severity Level: {result['severity_level']}")
    print(f"- Emergency Needed: {result['emergency_needed']}")
    
    # Test the emergency detection function directly
    emergency_check = check_emergency_needed(result['diagnosis'])
    print(f"- Direct Emergency Check: {emergency_check}")
    
    return result

def test_emergency_patterns():
    """Test emergency detection patterns directly"""
    
    print("\n=== Testing Emergency Detection Patterns ===")
    
    test_cases = [
        "緊急程度：是",
        "緊急程度：否", 
        "需要緊急就醫",
        "不需要緊急就醫",
        "建議立即前往急診室",
        "若症狀惡化，請立即就醫"
    ]
    
    for test_case in test_cases:
        result = check_emergency_needed(test_case)
        print(f"'{test_case}' -> Emergency: {result}")

if __name__ == "__main__":
    result = test_emergency_symptoms()
    test_emergency_patterns()
    
    print(f"\n=== Summary ===")
    print(f"Emergency needed from diagnosis: {result['emergency_needed']}")
    print("If this is False but you expect True, check:")
    print("1. AI response format - should include '緊急程度：是'")
    print("2. Emergency detection patterns in check_emergency_needed()")
    print("3. AI prompt instructions for emergency format")
