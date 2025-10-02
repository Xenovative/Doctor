#!/usr/bin/env python3
"""
Test script to set priority flags for some doctors and verify the priority system works
"""

import sqlite3
import sys

def test_priority_system():
    """Set priority flags for some doctors and test the system"""
    
    try:
        # Connect to database
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # First, check current state
        cursor.execute('SELECT COUNT(*) FROM doctors WHERE priority_flag > 0')
        priority_count = cursor.fetchone()[0]
        print(f"Current doctors with priority: {priority_count}")
        
        # Get some sample doctors to set priority
        cursor.execute('SELECT id, name_zh, specialty_zh FROM doctors LIMIT 10')
        sample_doctors = cursor.fetchall()
        
        if not sample_doctors:
            print("No doctors found in database!")
            return False
            
        print(f"\nSetting priority flags for test doctors:")
        
        # Set different priority levels for testing
        test_priorities = [
            (sample_doctors[0][0], 4, "Highest priority"), # Priority 4
            (sample_doctors[1][0], 3, "High priority"),    # Priority 3
            (sample_doctors[2][0], 2, "Medium priority"),  # Priority 2  
            (sample_doctors[3][0], 1, "Low priority"),     # Priority 1
        ]
        
        for doctor_id, priority, desc in test_priorities:
            cursor.execute('UPDATE doctors SET priority_flag = ? WHERE id = ?', (priority, doctor_id))
            doctor_name = next(d[1] for d in sample_doctors if d[0] == doctor_id)
            print(f"  - {doctor_name}: Priority {priority} ({desc})")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute('SELECT id, name_zh, priority_flag FROM doctors WHERE priority_flag > 0 ORDER BY priority_flag DESC')
        priority_doctors = cursor.fetchall()
        
        print(f"\nVerification - Doctors with priority flags:")
        for doctor_id, name, priority in priority_doctors:
            print(f"  - ID {doctor_id}: {name} (Priority: {priority})")
        
        print(f"\nPriority system test setup complete!")
        print(f"Total doctors with priority: {len(priority_doctors)}")
        
        return True
        
    except Exception as e:
        print(f"Error testing priority system: {e}")
        return False
    finally:
        if conn:
            conn.close()

def reset_priorities():
    """Reset all priority flags to 0"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE doctors SET priority_flag = 0')
        conn.commit()
        
        print("All priority flags reset to 0")
        return True
        
    except Exception as e:
        print(f"Error resetting priorities: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_priorities()
    else:
        test_priority_system()
