# enhanced_tools.py
from langchain_core.tools import tool
import datetime
import streamlit as st
from logger import setup_logger
from config import AppConfig
from typing import List, Dict, Any, Optional
from email_service import EmailService
import pytz
import random
from datetime import timedelta

logger = setup_logger(__name__)
config = AppConfig()

# Doctor availability data
DOCTOR_SCHEDULES = {
    "Dr. Smith": {
        "specialty": "General Practice",
        "available_days": ["Monday", "Wednesday", "Friday"],
        "hours": {"start": 9, "end": 17},
        "location": "Main Building, Room 101",
        "timezone": "America/New_York"
    },
    "Dr. Johnson": {
        "specialty": "Cardiology", 
        "available_days": ["Tuesday", "Thursday"],
        "hours": {"start": 10, "end": 16},
        "location": "Cardiac Wing, Room 205",
        "timezone": "America/New_York"
    },
    "Dr. Williams": {
        "specialty": "Dermatology",
        "available_days": ["Monday", "Tuesday", "Thursday", "Friday"],
        "hours": {"start": 8, "end": 15},
        "location": "Dermatology Center, Room 301",
        "timezone": "America/New_York"
    },
    "Dr. Brown": {
        "specialty": "Orthopedics",
        "available_days": ["Wednesday", "Thursday", "Friday"],
        "hours": {"start": 9, "end": 18},
        "location": "Sports Medicine Wing, Room 150",
        "timezone": "America/New_York"
    }
}

def validate_appointment_time(time: datetime.datetime, doctor_info: Dict[str, Any]) -> Optional[str]:
    """Validate appointment time against doctor's schedule."""
    try:
        # Convert to doctor's timezone
        doctor_tz = pytz.timezone(doctor_info.get("timezone", "America/New_York"))
        time_in_doctor_tz = time.astimezone(doctor_tz)
        
        # Check if date is in the past
        now = datetime.datetime.now(doctor_tz)
        if time_in_doctor_tz < now:
            return "Cannot book appointments in the past."
        
        # Check if day is available
        day_name = time_in_doctor_tz.strftime("%A")
        if day_name not in doctor_info["available_days"]:
            return f"Doctor is not available on {day_name}. Available days: {', '.join(doctor_info['available_days'])}"
        
        # Check if time is within working hours
        hour = time_in_doctor_tz.hour
        if not (doctor_info["hours"]["start"] <= hour < doctor_info["hours"]["end"]):
            return f"Doctor is only available from {doctor_info['hours']['start']}:00 to {doctor_info['hours']['end']}:00"
        
        return None
    except Exception as e:
        logger.error(f"Error validating appointment time: {e}")
        return "Error validating appointment time. Please try again."

def initialize_session_state():
    """Initialize session state with required data structures."""
    if 'appointments' not in st.session_state:
        st.session_state.appointments = []
    if 'email_service' not in st.session_state:
        st.session_state.email_service = EmailService()

@tool
def book_appointment(details: Dict[str, Any]) -> str:
    """Book an appointment with the provided details"""
    required_fields = ["patient_name", "doctor_name", "appointment_time"]
    
    for field in required_fields:
        if field not in details:
            return f"Missing required field: {field}"
    
    # Here you would typically save to a database
    return f"""Appointment confirmed!
Patient: {details['patient_name']}
Doctor: {details['doctor_name']}
Time: {details['appointment_time']}

A confirmation email will be sent shortly."""

@tool
def get_next_available_appointment(query: str = "") -> str:
    """Get the next available appointment slots"""
    current_time = datetime.now()
    available_slots = []
    
    # Generate some sample slots for the next 5 days
    for i in range(5):
        day = current_time + timedelta(days=i)
        if day.weekday() < 5:  # Weekdays only
            slots = [
                f"{day.strftime('%Y-%m-%d')} 09:00 AM",
                f"{day.strftime('%Y-%m-%d')} 11:00 AM",
                f"{day.strftime('%Y-%m-%d')} 02:00 PM",
                f"{day.strftime('%Y-%m-%d')} 04:00 PM"
            ]
            available_slots.extend(slots)
    
    response = "Available appointment slots:\n\n"
    for slot in available_slots[:5]:  # Show only next 5 slots
        response += f"📅 {slot}\n"
    
    return response

@tool
def cancel_appointment(details: Dict[str, Any]) -> str:
    """Cancel an existing appointment"""
    required_fields = ["appointment_id"]
    
    for field in required_fields:
        if field not in details:
            return f"Missing required field: {field}"
    
    # Here you would typically update a database
    return "Appointment cancelled successfully. A confirmation email will be sent shortly."

@tool
def get_doctor_availability(query: Dict[str, str]) -> str:
    """Get a specific doctor's availability"""
    doctor_name = query.get("doctor_name", "")
    current_time = datetime.now()
    
    # Get doctor's schedule from settings
    schedules = {
        "Dr. Smith": ["Monday", "Wednesday", "Friday"],
        "Dr. Johnson": ["Tuesday", "Thursday"],
        "Dr. Williams": ["Monday", "Tuesday", "Thursday", "Friday"],
        "Dr. Brown": ["Wednesday", "Thursday", "Friday"]
    }
    
    hours = {
        "Dr. Smith": "9:00 AM - 5:00 PM",
        "Dr. Johnson": "10:00 AM - 4:00 PM",
        "Dr. Williams": "8:00 AM - 3:00 PM",
        "Dr. Brown": "9:00 AM - 6:00 PM"
    }
    
    if doctor_name in schedules:
        return f"Available on: {', '.join(schedules[doctor_name])}\nHours: {hours[doctor_name]}"
    else:
        return "Doctor not found in schedule"

@tool
def get_doctor_list(query: str = "") -> str:
    """Get list of all available doctors"""
    doctors = {
        "Dr. Smith": "General Practice",
        "Dr. Johnson": "Cardiology",
        "Dr. Williams": "Dermatology",
        "Dr. Brown": "Orthopedics"
    }
    
    response = "Our Medical Team:\n\n"
    for doctor, specialty in doctors.items():
        response += f"👨‍⚕️ {doctor} - {specialty}\n"
    
    return response

@tool
def get_appointment_details(appointment_id: str) -> str:
    """Get details of a specific appointment"""
    # Here you would typically query a database
    return f"Appointment details for ID: {appointment_id}"

@tool
def reschedule_appointment(old_year: int, old_month: int, old_day: int, old_hour: int, old_minute: int,
                          new_year: int, new_month: int, new_day: int, new_hour: int, new_minute: int,
                          patient_name: str = ""):
    """
    Reschedule an existing appointment to a new time.
    """
    logger.debug(f"Rescheduling appointment from {old_year}-{old_month}-{old_day} to {new_year}-{new_month}-{new_day}")
    
    try:
        old_time = datetime.datetime(old_year, old_month, old_day, old_hour, old_minute)
        new_time = datetime.datetime(new_year, new_month, new_day, new_hour, new_minute)
        
        if 'appointments' not in st.session_state:
            return "No appointments found to reschedule."
        
        # Find the appointment to reschedule
        appointment_to_reschedule = None
        for i, appointment in enumerate(st.session_state.appointments):
            if appointment["time"] == old_time:
                if not patient_name or appointment["name"].lower() == patient_name.lower():
                    appointment_to_reschedule = (i, appointment)
                    break
        
        if not appointment_to_reschedule:
            return f"I couldn't find an appointment for {patient_name} at {old_time.strftime('%B %d, %Y at %I:%M %p')}."
        
        index, appointment = appointment_to_reschedule
        doctor_name = appointment.get('doctor_name', 'Dr. Smith')
        
        # Check if new time is available for the same doctor
        doctor_info = DOCTOR_SCHEDULES.get(doctor_name, DOCTOR_SCHEDULES['Dr. Smith'])
        new_day_name = new_time.strftime("%A")
        
        if new_day_name not in doctor_info["available_days"]:
            return f"{doctor_name} is not available on {new_day_name}. Available days: {', '.join(doctor_info['available_days'])}"
        
        if not (doctor_info["hours"]["start"] <= new_hour < doctor_info["hours"]["end"]):
            return f"{doctor_name} is available from {doctor_info['hours']['start']}:00 to {doctor_info['hours']['end']}:00"
        
        # Check for conflicts at new time
        for other_appointment in st.session_state.appointments:
            if (other_appointment["time"] == new_time and 
                other_appointment.get("doctor_name") == doctor_name and
                other_appointment != appointment):
                return f"Sorry, {doctor_name} already has an appointment at {new_time.strftime('%B %d, %Y at %I:%M %p')}"
        
        # Update the appointment
        old_time_str = appointment["time"].strftime('%B %d, %Y at %I:%M %p')
        appointment["time"] = new_time
        appointment["status"] = "rescheduled"
        
        logger.info(f"Rescheduled appointment for {appointment['name']} from {old_time_str} to {new_time.strftime('%B %d, %Y at %I:%M %p')}")
        
        return f"✅ Appointment rescheduled successfully!\n\n**Updated Details:**\n• Patient: {appointment['name']}\n• Doctor: {doctor_name}\n• Old Time: {old_time_str}\n• New Time: {new_time.strftime('%B %d, %Y at %I:%M %p')}\n• Location: {doctor_info['location']}\n• Type: {appointment['type']}\n\nYou will receive a new reminder for the updated time."
        
    except ValueError as e:
        logger.error(f"Invalid date/time for rescheduling: {e}")
        return "Please provide valid dates and times for rescheduling."
    except Exception as e:
        logger.exception(f"Error rescheduling appointment: {e}")
        return "I encountered an error while rescheduling the appointment. Please try again."