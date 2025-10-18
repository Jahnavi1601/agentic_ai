#!/usr/bin/env python3
"""
Database Viewer Script
This script allows you to view all data in the mental health database
"""

import sqlite3
from datetime import datetime

def view_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('mental_health.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("MENTAL HEALTH DATABASE VIEWER")
        print("=" * 60)
        
        # View Resources
        print("\n📋 RESOURCES:")
        print("-" * 40)
        cursor.execute('SELECT * FROM resources')
        resources = cursor.fetchall()
        for resource in resources:
            print(f"ID: {resource[0]}")
            print(f"Name: {resource[1]}")
            print(f"Contact: {resource[2]}")
            print(f"Description: {resource[3]}")
            print("-" * 40)
        
        # View Counselors
        print("\n👨‍⚕️ COUNSELORS:")
        print("-" * 40)
        cursor.execute('SELECT * FROM counselors')
        counselors = cursor.fetchall()
        for counselor in counselors:
            print(f"ID: {counselor[0]}")
            print(f"Name: {counselor[1]}")
            print(f"Specialty: {counselor[2]}")
            print(f"Available Days: {counselor[3]}")
            print("-" * 40)
        
        # View Appointments
        print("\n📅 APPOINTMENTS:")
        print("-" * 40)
        cursor.execute('SELECT * FROM appointments')
        appointments = cursor.fetchall()
        if appointments:
            for appointment in appointments:
                print(f"ID: {appointment[0]}")
                print(f"Counselor ID: {appointment[1]}")
                print(f"Student ID: {appointment[2]}")
                print(f"Appointment Time: {appointment[3]}")
                print(f"Booked At: {appointment[4]}")
                print("-" * 40)
        else:
            print("No appointments booked yet.")
        
        # Database Statistics
        print("\n📊 DATABASE STATISTICS:")
        print("-" * 40)
        cursor.execute('SELECT COUNT(*) FROM resources')
        resource_count = cursor.fetchone()[0]
        print(f"Total Resources: {resource_count}")
        
        cursor.execute('SELECT COUNT(*) FROM counselors')
        counselor_count = cursor.fetchone()[0]
        print(f"Total Counselors: {counselor_count}")
        
        cursor.execute('SELECT COUNT(*) FROM appointments')
        appointment_count = cursor.fetchone()[0]
        print(f"Total Appointments: {appointment_count}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    view_database()

