#!/usr/bin/env python3
"""
Test script to verify the priority sorting is working correctly
"""
import sqlite3
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the filter_doctors function
from app import filter_doctors

def test_priority_sorting():
    """Test that doctors with higher priority flags appear first"""
    print("Testing priority sorting...")
    
    # Test parameters
    recommended_specialty = "內科"
    language = "zh-TW"
    location = "香港"
    symptoms = "頭痛"
    ai_analysis = "測試分析"
    location_details = {
        'region': '香港島',
        'district': '中西區',
        'area': '中環'
    }
    
    # Get filtered doctors
    doctors = filter_doctors(
        recommended_specialty=recommended_specialty,
        language=language,
        location=location,
        symptoms=symptoms,
        ai_analysis=ai_analysis,
        location_details=location_details
    )
    
    print(f"\nFound {len(doctors)} doctors")
    print("\nTop 10 doctors (should be sorted by priority first):")
    print("Rank | Name | Priority | Location Priority | Score")
    print("-" * 60)
    
    for i, doctor in enumerate(doctors[:10], 1):
        name = doctor.get('name_zh', doctor.get('name', 'Unknown'))[:20]
        priority = doctor.get('priority_flag', 0)
        location_priority = doctor.get('location_priority', 0)
        score = doctor.get('match_score', 0)
        
        print(f"{i:4d} | {name:20s} | {priority:8d} | {location_priority:15d} | {score:5d}")
    
    # Check if highest priority doctors are at the top
    priority_4_doctors = [d for d in doctors if d.get('priority_flag', 0) == 4]
    priority_3_doctors = [d for d in doctors if d.get('priority_flag', 0) == 3]
    
    print(f"\nPriority 4 doctors found: {len(priority_4_doctors)}")
    print(f"Priority 3 doctors found: {len(priority_3_doctors)}")
    
    if priority_4_doctors:
        print("\nPriority 4 doctors:")
        for doctor in priority_4_doctors:
            name = doctor.get('name_zh', doctor.get('name', 'Unknown'))
            print(f"  - {name}")
    
    # Verify sorting is correct
    if len(doctors) > 1:
        is_sorted = True
        for i in range(len(doctors) - 1):
            current_priority = doctors[i].get('priority_flag', 0)
            next_priority = doctors[i + 1].get('priority_flag', 0)
            
            if current_priority < next_priority:
                is_sorted = False
                print(f"\nSORTING ERROR: Doctor at position {i+1} has lower priority ({current_priority}) than doctor at position {i+2} ({next_priority})")
                break
        
        if is_sorted:
            print("\n✅ Sorting is correct - doctors are properly ordered by priority!")
        else:
            print("\n❌ Sorting is incorrect!")
    
    return doctors

if __name__ == "__main__":
    test_priority_sorting()
