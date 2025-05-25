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
    
    try:
        
        doctor_tz = pytz.timezone(doctor_info.get("timezone", "America/New_York"))
        time_in_doctor_tz = time.astimezone(doctor_tz)
        
       
        now = datetime.datetime.now(doctor_tz)
        if time_in_doctor_tz < now:
            return "Cannot book appointments in the past."
        
       
        day_name = time_in_doctor_tz.strftime("%A")
        if day_name not in doctor_info["available_days"]:
            return f"Doctor is not available on {day_name}. Available days: {', '.join(doctor_info['available_days'])}"
        
       
        hour = time_in_doctor_tz.hour
        if not (doctor_info["hours"]["start"] <= hour < doctor_info["hours"]["end"]):
            return f"Doctor is only available from {doctor_info['hours']['start']}:00 to {doctor_info['hours']['end']}:00"
        
        return None
    except Exception as e:
        logger.error(f"Error validating appointment time: {e}")
        return "Error validating appointment time. Please try again."

def initialize_session_state():
   
    if 'appointments' not in st.session_state:
        st.session_state.appointments = []
    if 'email_service' not in st.session_state:
        st.session_state.email_service = EmailService()

@tool
def book_appointment(details: Dict[str, Any]) -> str:
    """
    Book a new appointment with the specified details.
    
    Args:
        details (Dict[str, Any]): Dictionary containing appointment details including patient_name, doctor_name, and appointment_time.
    
    Returns:
        str: Confirmation message with appointment details.
    """
    required_fields = ["patient_name", "doctor_name", "appointment_time"]
    
    for field in required_fields:
        if field not in details:
            return f"Missing required field: {field}"
    
   
    return f"""Appointment confirmed!
Patient: {details['patient_name']}
Doctor: {details['doctor_name']}
Time: {details['appointment_time']}

A confirmation email will be sent shortly."""

@tool
def get_next_available_appointment(query: str = "") -> str:
    """
    Get the next available appointment slots.
    
    Args:
        query (str, optional): Search query to filter available slots. Defaults to "".
    
    Returns:
        str: List of available appointment slots.
    """
    current_time = datetime.now()
    available_slots = []
    
   
    for i in range(5):
        day = current_time + timedelta(days=i)
        if day.weekday() < 5: 
            slots = [
                f"{day.strftime('%Y-%m-%d')} 09:00 AM",
                f"{day.strftime('%Y-%m-%d')} 11:00 AM",
                f"{day.strftime('%Y-%m-%d')} 02:00 PM",
                f"{day.strftime('%Y-%m-%d')} 04:00 PM"
            ]
            available_slots.extend(slots)
    
    response = "Available appointment slots:\n\n"
    for slot in available_slots[:5]:
        response += f"📅 {slot}\n"
    
    return response

@tool
def cancel_appointment(details: Dict[str, Any]) -> str:
    """
    Cancel an existing appointment.
    
    Args:
        details (Dict[str, Any]): Dictionary containing appointment details including appointment_id.
    
    Returns:
        str: Confirmation message for the cancelled appointment.
    """
    required_fields = ["appointment_id"]
    
    for field in required_fields:
        if field not in details:
            return f"Missing required field: {field}"
    
    
    return "Appointment cancelled successfully. A confirmation email will be sent shortly."

@tool
def get_doctor_availability(query: Dict[str, str]) -> str:
    """
    Get the availability schedule for a specific doctor.
    
    Args:
        query (Dict[str, str]): Dictionary containing doctor_name to check availability for.
    
    Returns:
        str: Doctor's availability schedule including days and hours.
    """
    doctor_name = query.get("doctor_name", "")
    current_time = datetime.now()
    
    
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
    """
    Get a list of all available doctors and their specialties.
    
    Args:
        query (str, optional): Search query to filter doctors. Defaults to "".
    
    Returns:
        str: List of doctors and their specialties.
    """
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
    """
    Get details for a specific appointment.
    
    Args:
        appointment_id (str): The unique identifier of the appointment.
    
    Returns:
        str: Details of the specified appointment.
    """
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
        doctor_info = DOCTOR_SCHEDULES.get(doctor_name, DOCTOR_SCHEDULES['Dr. Smith'])
        new_day_name = new_time.strftime("%A")
        
        if new_day_name not in doctor_info["available_days"]:
            return f"{doctor_name} is not available on {new_day_name}. Available days: {', '.join(doctor_info['available_days'])}"
        
        if not (doctor_info["hours"]["start"] <= new_hour < doctor_info["hours"]["end"]):
            return f"{doctor_name} is available from {doctor_info['hours']['start']}:00 to {doctor_info['hours']['end']}:00"
        
       
        for other_appointment in st.session_state.appointments:
            if (other_appointment["time"] == new_time and 
                other_appointment.get("doctor_name") == doctor_name and
                other_appointment != appointment):
                return f"Sorry, {doctor_name} already has an appointment at {new_time.strftime('%B %d, %Y at %I:%M %p')}"
        
        
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