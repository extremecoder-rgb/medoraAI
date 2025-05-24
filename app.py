# app.py - Updated with Multi-Agent System
import streamlit as st
from multi_agent_system import multi_agent_orchestrator
from langchain_core.messages import HumanMessage, AIMessage
from config import AppConfig
from logger import setup_logger
from utils import initialize_session_state, process_appointments, add_manual_appointment, cancel_appointment
from voice_agent import VoiceAgent
from audio_interface import audio_recorder, audio_player
import datetime
import json

logger = setup_logger(__name__)

def main():
    config = AppConfig()
    initialize_session_state()
    
    # Initialize voice agent
    if 'voice_agent' not in st.session_state:
        st.session_state.voice_agent = VoiceAgent()
        st.session_state.last_spoken_message = None  # Track last spoken message
    
    # Initialize conversation history for multi-agent system
    if 'multi_agent_conversation' not in st.session_state:
        st.session_state.multi_agent_conversation = []

    st.set_page_config(
        page_title="Smart Medical Appointment System", 
        page_icon="🏥", 
        layout="wide"
    )
    
    # Header
    st.title("🏥 Smart Medical Appointment System")
    st.markdown("*Powered by Multi-Agent AI - User Bot, Doctor Bot & Scheduler Bot*")
    
    # Create three columns for the layout
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("🤖 AI Assistant Chat")
        
        # Display conversation history
        for message in st.session_state.multi_agent_conversation:
            if isinstance(message, HumanMessage):
                st.chat_message("user").write(message.content)
            elif isinstance(message, AIMessage):
                st.chat_message("assistant").write(message.content)
                # Only speak if this is a new message and different from the last spoken message
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

        # Voice input section
        st.markdown("---")
        st.markdown("**🎤 Voice Input**")
        
        # Add audio recorder
        audio_recorder()
        
        # Handle audio data from browser
        if 'audio_data' not in st.session_state:
            st.session_state.audio_data = None
            
        # JavaScript to handle audio data
        js = """
        <script>
            window.addEventListener('message', function(event) {
                if (event.data.type === 'audioData') {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: event.data.data
                    }, '*');
                }
            });
        </script>
        """
        st.components.v1.html(js, height=0)
        
        # Process audio data if available
        if st.session_state.audio_data:
            try:
                voice_input = st.session_state.voice_agent.process_voice_command(st.session_state.audio_data)
                if voice_input:
                    st.text_area("🎙️ Voice Input Detected:", value=voice_input, height=100, disabled=True)
                    
                    voice_btn_col1, voice_btn_col2 = st.columns(2)
                    with voice_btn_col1:
                        if st.button("✅ Send Voice Input", type="primary"):
                            process_user_input(voice_input)
                            st.session_state.audio_data = None
                            st.rerun()
                    with voice_btn_col2:
                        if st.button("❌ Clear Voice Input"):
                            st.session_state.audio_data = None
                            st.rerun()
            except Exception as e:
                st.error(f"Voice processing failed: {e}")
                st.session_state.audio_data = None

        # Regular text input
        user_input = st.chat_input("💬 Type your message here (e.g., 'I need to book an appointment with a cardiologist')")
        if user_input:
            process_user_input(user_input)
            st.rerun()
        
        # Quick action buttons
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
            # Sort appointments by time
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
                    
                    # Quick cancel button
                    if st.button(f"Cancel This Appointment", key=f"cancel_{i}"):
                        if cancel_appointment(i):
                            st.success("Appointment cancelled!")
                            st.rerun()
        else:
            st.info("No appointments scheduled yet.")
            st.markdown("Use the chat to book your first appointment! 😊")
        
        # Appointment statistics
        st.markdown("---")
        st.markdown("**📊 Statistics:**")
        if st.session_state.appointments:
            today = datetime.datetime.now().date()
            today_appointments = [apt for apt in st.session_state.appointments if apt["time"].date() == today]
            upcoming_appointments = [apt for apt in st.session_state.appointments if apt["time"] > datetime.datetime.now()]
            
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric("Today", len(today_appointments))
            with stat_col2:
                st.metric("Upcoming", len(upcoming_appointments))

    with col3:
        st.subheader("⚙️ System Controls")
        
        # Agent status indicators
        st.markdown("**🤖 Agent Status:**")
        st.success("✅ User Bot: Active")
        st.success("✅ Doctor Bot: Active") 
        st.success("✅ Scheduler Bot: Active")
        
        # Manual appointment creation
        st.markdown("---")
        st.markdown("**➕ Manual Booking:**")
        with st.form("quick_appointment_form"):
            name = st.text_input("Name*", placeholder="Patient Name")
            email = st.text_input("Email", placeholder="patient@email.com")
            doctor = st.selectbox("Doctor", ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown"])
            apt_type = st.selectbox("Type", ["Consultation", "Follow-up", "Check-up", "Emergency"])
            date = st.date_input("Date", min_value=datetime.date.today())
            time = st.time_input("Time", value=datetime.time(9, 0))
            
            if st.form_submit_button("📅 Book Appointment", type="primary"):
                if name:
                    # Get doctor info for location
                    from enhanced_tools import DOCTOR_SCHEDULES
                    doctor_info = DOCTOR_SCHEDULES.get(doctor, {})
                    
                    add_manual_appointment(
                        person_name=name,
                        appointment_type=apt_type,
                        appointment_date=date,
                        appointment_time=time,
                        email=email,
                        doctor_name=doctor,
                        location=doctor_info.get('location', 'Main Office')
                    )
                    st.success(f"✅ Appointment booked for {name}!")
                    st.rerun()
                else:
                    st.error("Patient name is required!")
        
        # Debug information (collapsible)
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
        
    # Add user message to conversation
    st.session_state.multi_agent_conversation.append(HumanMessage(content=user_input))
    
    # Get response from multi-agent system
    response = multi_agent_orchestrator.process_user_message(user_input)
    
    # Add AI response to conversation
    st.session_state.multi_agent_conversation.append(AIMessage(content=response))

if __name__ == "__main__":
    main()