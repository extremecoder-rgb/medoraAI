import streamlit as st
import datetime
from logger import setup_logger
from email_service import EmailService

logger = setup_logger(__name__)

def initialize_session_state():
    if 'appointments' not in st.session_state:
        st.session_state.appointments = []
        logger.debug("Initialized empty appointments list in session state")
    
    if 'email_service' not in st.session_state:
        st.session_state.email_service = EmailService()
        logger.debug("Initialized email service in session state")

def process_appointments():
    logger.debug(f"Appointments in session state: {st.session_state.appointments}")
    for appointment in st.session_state.appointments:
        logger.debug(f"Processing appointment: {appointment}")
        st.write(f"Debug: Processing appointment: {appointment}")
        st.write(
            f"{appointment['name']} - {appointment['type']} on {appointment['time'].strftime('%B %d, %Y at %I:%M %p')}")

    if not st.session_state.appointments:
        st.write("No appointments scheduled.")
        logger.debug("No appointments found in session state")

def add_manual_appointment(person_name, appointment_type, appointment_date, appointment_time, email=None, doctor_name=None, location=None):
    new_appointment = {
        "name": person_name,
        "type": appointment_type,
        "time": datetime.datetime.combine(appointment_date, appointment_time),
        "email": email,
        "doctor_name": doctor_name,
        "location": location,
        "reminder_sent": False
    }
    st.session_state.appointments.append(new_appointment)
    logger.debug(f"Manually added appointment: {new_appointment}")
    
    # Send booking confirmation email if email is provided
    if email:
        st.session_state.email_service.send_booking_confirmation(new_appointment)

def cancel_appointment(appointment_index):
    """Cancel an appointment and send cancellation email"""
    if 0 <= appointment_index < len(st.session_state.appointments):
        appointment = st.session_state.appointments.pop(appointment_index)
        logger.debug(f"Cancelled appointment: {appointment}")
        
        # Send cancellation email if email is provided
        if appointment.get("email"):
            st.session_state.email_service.send_cancellation_confirmation(appointment)
        
        return True
    return False