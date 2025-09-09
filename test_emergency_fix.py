#!/usr/bin/env python3
"""Test script to verify emergency detection and specialty extraction fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import check_emergency_needed, extract_specialty_from_diagnosis, extract_severity_from_diagnosis

def test_emergency_detection():
    print("=== Testing Emergency Detection ===")
    
    # Test case 1: Non-emergency with conditional advice
    test1 = """
    可能診斷：
    1. 高血壓
    2. 貧血
    3. 睡眠障礙

    建議專科：內科

    嚴重程度：中等

    緊急程度：不需要緊急就醫，但應及時看醫生

    建議：病人應多休息，避免過度勞累，並保持均衡飲食。若症狀持續或惡化，應立即就醫。
    """
    
    result1 = check_emergency_needed(test1)
    print(f"Test 1 (Non-emergency): {result1} (should be False)")
    
    # Test case 2: True emergency
    test2 = """
    可能診斷：心肌梗塞
    建議專科：心臟科
    嚴重程度：嚴重
    緊急程度：需要緊急就醫，請立即前往急診室
    """
    
    result2 = check_emergency_needed(test2)
    print(f"Test 2 (True emergency): {result2} (should be True)")
    
    # Test case 3: Dermatology case
    test3 = """
    可能診斷：濕疹
    建議專科：皮膚科
    嚴重程度：輕微
    緊急程度：不需要緊急就醫
    """
    
    result3 = check_emergency_needed(test3)
    print(f"Test 3 (Dermatology): {result3} (should be False)")

def test_specialty_extraction():
    print("\n=== Testing Specialty Extraction ===")
    
    # Test case 1: Internal Medicine
    test1 = """
    建議專科：內科
    嚴重程度：中等
    """
    result1 = extract_specialty_from_diagnosis(test1)
    print(f"Test 1 (Internal Medicine): {result1}")
    
    # Test case 2: Dermatology
    test2 = """
    建議專科：皮膚科
    嚴重程度：輕微
    """
    result2 = extract_specialty_from_diagnosis(test2)
    print(f"Test 2 (Dermatology): {result2}")
    
    # Test case 3: Cardiology
    test3 = """
    建議專科：心臟科
    嚴重程度：嚴重
    """
    result3 = extract_specialty_from_diagnosis(test3)
    print(f"Test 3 (Cardiology): {result3}")
    
    # Test case 4: English specialty
    test4 = """
    Recommended specialty: Orthopedics
    Severity: Moderate
    """
    result4 = extract_specialty_from_diagnosis(test4)
    print(f"Test 4 (Orthopedics): {result4}")

if __name__ == "__main__":
    test_emergency_detection()
    test_specialty_extraction()
