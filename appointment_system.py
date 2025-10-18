from datetime import datetime, timedelta
import json

class AppointmentSystem:
    def __init__(self):
        # Mock database of available counselors and their schedules
        self.counselors = {
            "Dr. Smith": {"specialty": "General Mental Health", "available_days": ["Monday", "Wednesday", "Friday"]},
            "Dr. Johnson": {"specialty": "Anxiety & Depression", "available_days": ["Tuesday", "Thursday"]},
            "Dr. Williams": {"specialty": "Stress Management", "available_days": ["Monday", "Tuesday", "Thursday"]}
        }
        
        # Mock appointments database
        self.appointments = {}
        
    def get_available_slots(self, counselor_name, date=None):
        """Get available appointment slots for a counselor on a specific date."""
        if date is None:
            date = datetime.now()
            
        # Check if counselor exists
        if counselor_name not in self.counselors:
            return []
            
        # Check if counselor works on this day
        day_name = date.strftime("%A")
        if day_name not in self.counselors[counselor_name]["available_days"]:
            return []
            
        # Generate available slots (9 AM to 4 PM, 1-hour slots)
        available_slots = []
        start_time = datetime.combine(date.date(), datetime.strptime("09:00", "%H:%M").time())
        end_time = datetime.combine(date.date(), datetime.strptime("16:00", "%H:%M").time())
        
        current_slot = start_time
        while current_slot < end_time:
            slot_key = f"{counselor_name}_{current_slot.strftime('%Y-%m-%d_%H:%M')}"
            if slot_key not in self.appointments:
                available_slots.append(current_slot.strftime("%Y-%m-%d %H:%M"))
            current_slot += timedelta(hours=1)
            
        return available_slots
        
    def book_appointment(self, counselor_name, datetime_str, student_id):
        """Book an appointment with a counselor."""
        try:
            appointment_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            slot_key = f"{counselor_name}_{appointment_time.strftime('%Y-%m-%d_%H:%M')}"
            
            # Check if slot is available
            if slot_key in self.appointments:
                return False, "This slot is already booked."
                
            # Check if counselor works on this day
            day_name = appointment_time.strftime("%A")
            if day_name not in self.counselors[counselor_name]["available_days"]:
                return False, f"{counselor_name} is not available on {day_name}s."
            
            # Book the appointment
            self.appointments[slot_key] = {
                "student_id": student_id,
                "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            return True, {
                "counselor": counselor_name,
                "appointment_time": datetime_str,
                "confirmation_code": slot_key
            }
            
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD HH:MM format."
            
    def get_counselors(self):
        """Get list of all counselors and their specialties."""
        return {name: info["specialty"] for name, info in self.counselors.items()}