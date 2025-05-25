import streamlit as st
from multi_agent_system import multi_agent_orchestrator
from langchain_core.messages import HumanMessage, AIMessage
from config import AppConfig
from logger import setup_logger
from utils import initialize_session_state, process_appointments, add_manual_appointment, cancel_appointment
from voice_agent import VoiceAgent
from audio_interface import audio_recorder, audio_player
from email_service import email_service
import datetime
import json
import re

logger = setup_logger(__name__)

def main():
    config = AppConfig()
    initialize_session_state()

    if 'voice_agent' not in st.session_state:
        st.session_state.voice_agent = VoiceAgent()
        st.session_state.last_spoken_message = None  
  
    if 'multi_agent_conversation' not in st.session_state:
        st.session_state.multi_agent_conversation = []

    st.set_page_config(
        page_title="Smart Medical Appointment System", 
        page_icon="🏥", 
        layout="wide"
    )
    
   
    st.title("🏥 Smart Medical Appointment System")
    st.markdown("*Powered by Multi-Agent AI - User Bot, Doctor Bot & Scheduler Bot*")
    
    # Create three columns for the layout
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("🤖 AI Assistant Chat")
        
        
        for message in st.session_state.multi_agent_conversation:
            if isinstance(message, HumanMessage):
                st.chat_message("user").write(message.content)
            elif isinstance(message, AIMessage):
                st.chat_message("assistant").write(message.content)
               
                if (message == st.session_state.multi_agent_conversation[-1] and 
                    message.content != st.session_state.last_spoken_message):
                    try:
                        if hasattr(st.session_state, 'voice_agent'):
                            audio_data = st.session_state.voice_agent.text_to_speech(message.content)
                            if audio_data:
                                audio_player(audio_data)
                                st.session_state.last_spoken_message = message.content
                    except Exception as e:
                        logger.warning(f"Text-to-speech failed: {e}")

        
        chat_col1, chat_col2 = st.columns([10, 1])
        with chat_col1:
            user_input = st.chat_input("💬 Type your message here (e.g., 'I need to book an appointment with a cardiologist')")
        with chat_col2:
            if st.button("🎤", help="Record voice input"):
                st.session_state.show_audio_recorder = True

       
        if st.session_state.get('show_audio_recorder', False):
            st.markdown("**🎤 Speak now and stop when done...**")
            from st_audiorec import st_audiorec
            audio_data = st_audiorec()
            if audio_data is not None:
               
                import tempfile
                import os
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_wav.write(audio_data)
                temp_wav.close()
                try:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(temp_wav.name) as source:
                        audio = recognizer.record(source)
                        text = recognizer.recognize_google(audio)
                    process_user_input(text)
                    st.session_state.show_audio_recorder = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Voice processing failed: {e}")
                    st.session_state.show_audio_recorder = False
                finally:
                    os.unlink(temp_wav.name)

        if user_input:
           
            if st.session_state.get('awaiting_email_for_appointment', False):
                
                email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                if re.match(email_pattern, user_input.strip()):
                    
                    if st.session_state.appointments:
                        st.session_state.appointments[-1]['email'] = user_input.strip()
                       
                        email_service.send_booking_confirmation(st.session_state.appointments[-1])
                        st.session_state.awaiting_email_for_appointment = False
                        st.success("Confirmation email sent!")
                        st.rerun()
                    else:
                        st.session_state.awaiting_email_for_appointment = False
                        st.error("No appointment found to attach this email to.")
                else:
                    st.warning("Please enter a valid email address to receive your confirmation.")
            else:
                process_user_input(user_input)
                
                if (
                    st.session_state.appointments
                    and not st.session_state.appointments[-1].get('email')
                    and st.session_state.appointments[-1].get('status', '').lower() == 'confirmed'
                    and not st.session_state.get('awaiting_email_for_appointment', False)
                ):
                    st.session_state.awaiting_email_for_appointment = True
                    st.warning("Please provide your email address to receive a confirmation email for your appointment.")
                st.rerun()
        
       
        if (
            st.session_state.appointments
            and not st.session_state.appointments[-1].get('email')
            and st.session_state.appointments[-1].get('status', '').lower() == 'confirmed'
            and not st.session_state.get('email_sent_for_last_appointment', False)
        ):
            st.markdown('---')
            st.info('Please enter your email address to receive a confirmation email for your recent appointment:')
            email_input = st.text_input('Email for confirmation', key='ai_booking_email')
            if st.button('Send Confirmation Email'):
                import re
                email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                if re.match(email_pattern, email_input.strip()):
                    st.session_state.appointments[-1]['email'] = email_input.strip()
                    email_service.send_booking_confirmation(st.session_state.appointments[-1])
                    st.session_state.email_sent_for_last_appointment = True
                    st.success('Confirmation email sent!')
                    st.rerun()
                else:
                    st.warning('Please enter a valid email address.')
        
      
        st.markdown("---")
        st.markdown("**🚀 Quick Actions:**")
        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        
        with quick_col1:
            if st.button("📅 Book Appointment"):
                process_user_input("I would like to book an appointment")
                st.rerun()
        
        with quick_col2:
            if st.button("🔍 Check Availability"):
                process_user_input("What are the next available appointments?")
                st.rerun()
        
        with quick_col3:
            if st.button("👨‍⚕️ Find Doctor"):
                process_user_input("Show me available doctors")
                st.rerun()
                
        with quick_col4:
            if st.button("❌ Cancel Appointment"):
                process_user_input("I need to cancel an appointment")
                st.rerun()

    with col2:
        st.subheader("📋 Current Appointments")
        
        if st.session_state.appointments:
            
            sorted_appointments = sorted(st.session_state.appointments, key=lambda x: x["time"])
            
            for i, appointment in enumerate(sorted_appointments):
                with st.expander(f"📅 {appointment['name']} - {appointment['time'].strftime('%m/%d %I:%M %p')}"):
                    st.write(f"**Patient:** {appointment['name']}")
                    st.write(f"**Doctor:** {appointment.get('doctor_name', 'Not assigned')}")
                    st.write(f"**Specialty:** {appointment.get('doctor_specialty', 'General')}")
                    st.write(f"**Date & Time:** {appointment['time'].strftime('%A, %B %d, %Y at %I:%M %p')}")
                    st.write(f"**Type:** {appointment['type']}")
                    st.write(f"**Location:** {appointment.get('location', 'Main Office')}")
                    st.write(f"**Status:** {appointment.get('status', 'Confirmed').title()}")
                    
                    if appointment.get('email'):
                        st.write(f"**Email:** {appointment['email']}")
                    
                    
                    if st.button(f"Cancel This Appointment", key=f"cancel_{i}"):
                        if cancel_appointment(i):
                            st.success("Appointment cancelled!")
                            st.rerun()
        else:
            st.info("No appointments scheduled yet.")
            st.markdown("Use the chat to book your first appointment! 😊")

    with col3:
        st.subheader("⚙️ System Controls")
        st.markdown("**🤖 Agent Status:**")
        st.success("✅ User Bot: Active")
        st.success("✅ Doctor Bot: Active") 
        st.success("✅ Scheduler Bot: Active")
        
        
        st.markdown("---")
        st.markdown("**➕ Manual Booking:**")
        with st.form("quick_appointment_form"):
            name = st.text_input("Name*", placeholder="Patient Name")
            email = st.text_input("Email*", placeholder="patient@email.com")
            doctor = st.selectbox("Doctor", ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown"])
            apt_type = st.selectbox("Type", ["Consultation", "Follow-up", "Check-up", "Emergency"])
            date = st.date_input("Date", min_value=datetime.date.today())
            time = st.time_input("Time", value=datetime.time(9, 0))
            
            
            doctor_schedules = {
                "Dr. Smith": {"location": "Main Building, Room 101"},
                "Dr. Johnson": {"location": "Cardiac Wing, Room 205"},
                "Dr. Williams": {"location": "Dermatology Center, Room 301"},
                "Dr. Brown": {"location": "Sports Medicine Wing, Room 150"}
            }
            
            if st.form_submit_button("📅 Book Appointment", type="primary"):
                if name and email:
                    doctor_info = doctor_schedules.get(doctor, {})
                    add_manual_appointment(
                        person_name=name,
                        appointment_type=apt_type,
                        appointment_date=date,
                        appointment_time=time,
                        email=email,
                        doctor_name=doctor,
                        location=doctor_info.get('location', 'Main Office')
                    )
                   
                    appointment_data = {
                        "name": name,
                        "email": email,
                        "doctor_name": doctor,
                        "type": apt_type,
                        "time": datetime.datetime.combine(date, time),
                        "location": doctor_info.get('location', 'Main Office')
                    }
                    if email_service.send_appointment_confirmation(appointment_data):
                        st.success(f"✅ Appointment booked for {name}! Confirmation email sent.")
                    else:
                        st.warning(f"✅ Appointment booked for {name}, but email confirmation failed.")
                    st.rerun()
                else:
                    st.error("Patient name and email are required!")
        
    
        with st.expander("🔧 Debug Information"):
            st.write("**Session State:**")
            st.json({
                "appointments_count": len(st.session_state.appointments),
                "conversation_length": len(st.session_state.multi_agent_conversation),
                "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            if st.button("🗑️ Clear All Data"):
                st.session_state.appointments = []
                st.session_state.multi_agent_conversation = []
                st.success("All data cleared!")
                st.rerun()

def process_user_input(user_input: str):
    """Process user input and update conversation history."""
    if not user_input.strip():
        return
        
    
    st.session_state.multi_agent_conversation.append(HumanMessage(content=user_input))
    
    
    response = multi_agent_orchestrator.process_user_message(user_input)
    
    
    st.session_state.multi_agent_conversation.append(AIMessage(content=response))

if __name__ == "__main__":
    main()