import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class MySQLManager:
    def __init__(self):
        # Get MySQL connection details from environment variables
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'mental_health_support')
        }
    
    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise e
    
    def get_resources(self):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT * FROM resources')
            resources = {}
            for row in cursor.fetchall():
                resources[row['id']] = {
                    'name': row['name'],
                    'contact': row['contact'],
                    'description': row['description']
                }
            return resources
        except Error as e:
            print(f"Error getting resources: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def get_counselors(self):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT * FROM counselors')
            counselors = {}
            for row in cursor.fetchall():
                counselors[row['name']] = {
                    'specialty': row['specialty'],
                    'available_days': row['available_days'].split(',')
                }
            return counselors
        except Error as e:
            print(f"Error getting counselors: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def book_appointment(self, counselor_name, datetime_str, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get counselor ID
            cursor.execute('SELECT id, available_days FROM counselors WHERE name = %s', (counselor_name,))
            counselor = cursor.fetchone()
            
            if not counselor:
                return False, "Counselor not found."
                
            counselor_id, available_days = counselor
            available_days = available_days.split(',')
            
            # Check if slot is available
            try:
                appointment_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return False, "Invalid date format. Please use YYYY-MM-DD HH:MM format."
                
            day_name = appointment_time.strftime("%A")
            
            if day_name not in available_days:
                return False, f"{counselor_name} is not available on {day_name}s."
            
            # Check if slot is already booked
            cursor.execute('''SELECT COUNT(*) FROM appointments 
                            WHERE counselor_id = %s AND appointment_time = %s''',
                         (counselor_id, datetime_str))
            
            if cursor.fetchone()[0] > 0:
                return False, "This slot is already booked."
            
            # Book the appointment
            appointment_id = f"{counselor_id}_{appointment_time.strftime('%Y-%m-%d_%H:%M')}"
            cursor.execute('''INSERT INTO appointments (id, counselor_id, student_id, appointment_time, booked_at)
                            VALUES (%s, %s, %s, %s, %s)''',
                         (appointment_id, counselor_id, student_id, datetime_str, 
                          datetime.now().strftime("%Y-%m-%d %H:%M")))
            
            conn.commit()
            
            return True, {
                "counselor": counselor_name,
                "appointment_time": datetime_str,
                "confirmation_code": appointment_id
            }
            
        except Error as e:
            conn.rollback()
            print(f"Database error: {str(e)}")
            return False, f"Database error: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def get_available_slots(self, counselor_name, date=None):
        if date is None:
            date = datetime.now()
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get counselor's available days
            cursor.execute('SELECT id, available_days FROM counselors WHERE name = %s', (counselor_name,))
            counselor = cursor.fetchone()
            
            if not counselor:
                return []
                
            counselor_id, available_days = counselor
            available_days = available_days.split(',')
            
            # Check if counselor works on this day
            day_name = date.strftime("%A")
            if day_name not in available_days:
                return []
            
            # Generate all possible slots
            available_slots = []
            start_time = datetime.combine(date.date(), datetime.strptime("09:00", "%H:%M").time())
            end_time = datetime.combine(date.date(), datetime.strptime("16:00", "%H:%M").time())
            
            current_slot = start_time
            while current_slot < end_time:
                slot_str = current_slot.strftime("%Y-%m-%d %H:%M")
                
                # Check if slot is already booked
                cursor.execute('''SELECT COUNT(*) FROM appointments 
                                WHERE counselor_id = %s AND appointment_time = %s''',
                             (counselor_id, slot_str))
                             
                if cursor.fetchone()[0] == 0:
                    available_slots.append(slot_str)
                    
                current_slot += timedelta(hours=1)
            
            return available_slots
            
        except Error as e:
            print(f"Database error: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()