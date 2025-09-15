#!/usr/bin/env python3
"""
Quick script to check the actual database values for created_at
"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('admin_data.db')
cursor = conn.cursor()

print("Current admin_users created_at values:")
cursor.execute("SELECT id, username, created_at FROM admin_users ORDER BY id")
users = cursor.fetchall()

for user in users:
    user_id, username, created_at = user
    print(f"ID: {user_id}, User: {username}")
    print(f"  Raw value: {repr(created_at)}")
    print(f"  Type: {type(created_at)}")
    
    if created_at:
        try:
            # Try parsing as different formats
            if isinstance(created_at, str):
                # Try parsing as datetime string
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                print(f"  Parsed datetime: {dt}")
            elif isinstance(created_at, (int, float)):
                # Try parsing as timestamp
                dt = datetime.fromtimestamp(created_at)
                print(f"  Parsed timestamp: {dt}")
        except Exception as e:
            print(f"  Parse error: {e}")
    print()

conn.close()
