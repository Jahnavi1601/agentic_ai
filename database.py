import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('mental_health.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS resources
                 (id TEXT PRIMARY KEY,
                  name TEXT,
                  contact TEXT,
                  description TEXT)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS counselors
                 (id TEXT PRIMARY KEY,
                  name TEXT,
                  specialty TEXT,
                  available_days TEXT)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS appointments
                 (id TEXT PRIMARY KEY,
                  counselor_id TEXT,
                  student_id TEXT,
                  appointment_time TEXT,
                  booked_at TEXT,
                  FOREIGN KEY (counselor_id) REFERENCES counselors (id))''')
    
    # Insert initial resources if table is empty
    c.execute('SELECT COUNT(*) FROM resources')
    if c.fetchone()[0] == 0:
        resources = [
            ('emergency', 'Emergency Services', '911', 'For immediate emergency assistance'),
            ('crisis_line', 'Crisis Hotline', '1-800-273-8255', '24/7 confidential support'),
            ('counseling', 'University Counseling Center', 'Contact your university\'s counseling center', 'Professional counseling services for students')
        ]
        c.executemany('INSERT INTO resources VALUES (?,?,?,?)', resources)
    
    # Insert initial counselors if table is empty
    c.execute('SELECT COUNT(*) FROM counselors')
    if c.fetchone()[0] == 0:
        counselors = [
            ('smith', 'Dr. Smith', 'General Mental Health', 'Monday,Wednesday,Friday'),
            ('johnson', 'Dr. Johnson', 'Anxiety & Depression', 'Tuesday,Thursday'),
            ('williams', 'Dr. Williams', 'Stress Management', 'Monday,Tuesday,Thursday')
        ]
        c.executemany('INSERT INTO counselors VALUES (?,?,?,?)', counselors)
    
    conn.commit()
    conn.close()

class DatabaseManager:
    def __init__(self):
        self.db_name = 'mental_health.db'
        init_db()
    
    def get_resources(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT * FROM resources')
        resources = {}
        for row in c.fetchall():
            resources[row[0]] = {
                'name': row[1],
                'contact': row[2],
                'description': row[3]
            }
        conn.close()
        return resources
    
    def get_counselors(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT * FROM counselors')
        counselors = {}
        for row in c.fetchall():
            counselors[row[1]] = {
                'specialty': row[2],
                'available_days': row[3].split(',')
            }
        conn.close()
        return counselors
    
    def book_appointment(self, counselor_name, datetime_str, student_id):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Get counselor ID
            c.execute('SELECT id, available_days FROM counselors WHERE name = ?', (counselor_name,))
            counselor = c.fetchone()
            if not counselor:
                return False, "Counselor not found."
                
            counselor_id, available_days = counselor
            available_days = available_days.split(',')
            
            # Check if slot is available
            appointment_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            day_name = appointment_time.strftime("%A")
            
            if day_name not in available_days:
                return False, f"{counselor_name} is not available on {day_name}s."
            
            # Check if slot is already booked
            c.execute('''SELECT COUNT(*) FROM appointments 
                        WHERE counselor_id = ? AND appointment_time = ?''',
                     (counselor_id, datetime_str))
                     
            if c.fetchone()[0] > 0:
                return False, "This slot is already booked."
            
            # Book the appointment
            appointment_id = f"{counselor_id}_{appointment_time.strftime('%Y-%m-%d_%H:%M')}"
            c.execute('''INSERT INTO appointments (id, counselor_id, student_id, appointment_time, booked_at)
                        VALUES (?, ?, ?, ?, ?)''',
                     (appointment_id, counselor_id, student_id, datetime_str, datetime.now().strftime("%Y-%m-%d %H:%M")))
            
            conn.commit()
            conn.close()
            
            return True, {
                "counselor": counselor_name,
                "appointment_time": datetime_str,
                "confirmation_code": appointment_id
            }
            
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD HH:MM format."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
            
    def get_available_slots(self, counselor_name, date=None):
        if date is None:
            date = datetime.now()
            
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Get counselor's available days
        c.execute('SELECT id, available_days FROM counselors WHERE name = ?', (counselor_name,))
        counselor = c.fetchone()
        
        if not counselor:
            conn.close()
            return []
            
        counselor_id, available_days = counselor
        available_days = available_days.split(',')
        
        # Check if counselor works on this day
        day_name = date.strftime("%A")
        if day_name not in available_days:
            conn.close()
            return []
        
        # Generate all possible slots
        available_slots = []
        start_time = datetime.combine(date.date(), datetime.strptime("09:00", "%H:%M").time())
        end_time = datetime.combine(date.date(), datetime.strptime("16:00", "%H:%M").time())
        
        current_slot = start_time
        while current_slot < end_time:
            slot_str = current_slot.strftime("%Y-%m-%d %H:%M")
            
            # Check if slot is already booked
            c.execute('''SELECT COUNT(*) FROM appointments 
                        WHERE counselor_id = ? AND appointment_time = ?''',
                     (counselor_id, slot_str))
                     
            if c.fetchone()[0] == 0:
                available_slots.append(slot_str)
                
            current_slot = datetime.fromtimestamp(current_slot.timestamp() + 3600)  # Add 1 hour
        
        conn.close()
        return available_slots