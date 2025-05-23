import streamlit as st
from agent import receive_message_from_caller, CONVERSATION
from langchain_core.messages import HumanMessage
from config import AppConfig
from logger import setup_logger
from utils import initialize_session_state, process_appointments, add_manual_appointment, cancel_appointment
from voice_agent import VoiceAgent

logger = setup_logger(__name__)


def main():
    config = AppConfig()
    initialize_session_state()
    
    # Initialize voice agent
    if 'voice_agent' not in st.session_state:
        st.session_state.voice_agent = VoiceAgent()

    st.set_page_config(layout="wide")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Appointment Manager")
        for message in CONVERSATION:
            if isinstance(message, HumanMessage):
                st.chat_message("user").write(message.content)
            else:
                st.chat_message("assistant").write(message.content)
                # Convert assistant's response to speech
                st.session_state.voice_agent.text_to_speech(message.content)

        # Add voice input button
        if st.button("🎤 Start Voice Input"):
            with st.spinner("Listening..."):
                voice_input = st.session_state.voice_agent.process_voice_command()
                if voice_input:
                    st.session_state.voice_input = voice_input
                    st.rerun()

        # Display voice input if available
        if 'voice_input' in st.session_state:
            st.text_input("Voice Input", value=st.session_state.voice_input, disabled=True)
            if st.button("Send Voice Input"):
                receive_message_from_caller(st.session_state.voice_input)
                del st.session_state.voice_input
                st.rerun()

        # Regular text input
        user_input = st.chat_input("Type message here")
        if user_input:
            logger.debug(f"Received user input: {user_input}")
            receive_message_from_caller(user_input)
            st.rerun()

    with col2:
        st.header("Backend Trace")
        st.write("Debug: Session State Contents")
        st.write(st.session_state)

        st.write("Debug: Appointments List")
        st.write(st.session_state.appointments)

        process_appointments()

        # Add a form to manually create an appointment
        st.subheader("Create Appointment")
        with st.form("appointment_form"):
            person_name = st.text_input("Name")
            email = st.text_input("Email")
            doctor_name = st.text_input("Doctor Name")
            appointment_type = st.text_input("Appointment Type")
            appointment_date = st.date_input("Date")
            appointment_time = st.time_input("Time")
            location = st.text_input("Location")
            submit_button = st.form_submit_button("Add Appointment")

            if submit_button:
                add_manual_appointment(
                    person_name=person_name,
                    appointment_type=appointment_type,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    email=email,
                    doctor_name=doctor_name,
                    location=location
                )
                st.rerun()

        # Add appointment cancellation section
        st.subheader("Cancel Appointment")
        if st.session_state.appointments:
            appointment_index = st.selectbox(
                "Select appointment to cancel",
                range(len(st.session_state.appointments)),
                format_func=lambda x: f"{st.session_state.appointments[x]['name']} - {st.session_state.appointments[x]['time'].strftime('%B %d, %Y at %I:%M %p')}"
            )
            if st.button("Cancel Selected Appointment"):
                if cancel_appointment(appointment_index):
                    st.success("Appointment cancelled successfully!")
                    st.rerun()
                else:
                    st.error("Failed to cancel appointment")


if __name__ == "__main__":
    main()