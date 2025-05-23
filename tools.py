from langchain_core.tools import tool
import datetime
import streamlit as st
from logger import setup_logger
from config import AppConfig

logger = setup_logger(__name__)
config = AppConfig()

@tool
def book_appointment(person_name: str, appointment_type: str, appointment_year: int, appointment_month: int,
                     appointment_day: int, appointment_hour: int, appointment_minute: int):
    """
    Book an appointment with the given details.
    """
    logger.debug(f"Attempting to book appointment for {person_name}")
    time = datetime.datetime(appointment_year, appointment_month, appointment_day, appointment_hour, appointment_minute)
    new_appointment = {
        "name": person_name,
        "type": appointment_type,
        "time": time
    }

    if 'appointments' not in st.session_state:
        logger.warning("appointments not in session state, initializing")
        st.session_state.appointments = []

    st.session_state.appointments.append(new_appointment)

    logger.info(f"Booked appointment: {new_appointment}")
    logger.debug(f"Current appointments: {st.session_state.appointments}")

    return f"Appointment booked for {person_name} ({appointment_type}) on {time.strftime('%B %d, %Y at %I:%M %p')}. Is there anything else you need?"

@tool
def get_next_available_appointment():
    """
    Get the next available appointment slot.
    """
    logger.debug("Checking for next available appointment")
    if 'appointments' not in st.session_state or not st.session_state.appointments:
        logger.info("No appointments found")
        return "All time slots are currently available. When would you like to schedule your appointment?"

    current_time = datetime.datetime.now()
    next_slot = current_time + datetime.timedelta(minutes=(30 - current_time.minute % 30))
    while any(appointment["time"] == next_slot for appointment in st.session_state.appointments):
        next_slot += datetime.timedelta(minutes=30)

    logger.info(f"Next available slot: {next_slot}")
    return f"The next available appointment slot is on {next_slot.strftime('%B %d, %Y at %I:%M %p')}. Would you like to book this time?"

@tool
def cancel_appointment(appointment_year: int, appointment_month: int, appointment_day: int, appointment_hour: int,
                       appointment_minute: int):
    """
    Cancel an appointment at the given date and time.
    """
    logger.debug(
        f"Attempting to cancel appointment at {appointment_year}-{appointment_month}-{appointment_day} {appointment_hour}:{appointment_minute}")
    time = datetime.datetime(appointment_year, appointment_month, appointment_day, appointment_hour, appointment_minute)

    if 'appointments' not in st.session_state:
        logger.warning("No appointments in session state")
        return "There are no appointments scheduled."

    for appointment in st.session_state.appointments:
        if appointment["time"] == time:
            cancelled_appointment = st.session_state.appointments.remove(appointment)
            logger.info(f"Cancelled appointment: {cancelled_appointment}")
            return f"The appointment for {cancelled_appointment['name']} ({cancelled_appointment['type']}) on {time.strftime('%B %d, %Y at %I:%M %p')} has been cancelled. Is there anything else I can help you with?"

    logger.warning(f"No appointment found at {time}")
    return f"I'm sorry, but I couldn't find an appointment scheduled for {time.strftime('%B %d, %Y at %I:%M %p')}. Would you like to check for a different time?"
