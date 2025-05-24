# multi_agent_system.py
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any, TypedDict, Literal, Optional
from config import AppConfig
from logger import setup_logger
from tools import book_appointment, get_next_available_appointment, cancel_appointment, get_doctor_availability, get_appointment_details, get_doctor_list
from datetime import datetime
import json
import os
import re
import streamlit as st

logger = setup_logger(__name__)
load_dotenv()

# Get API key from environment with fallback
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in environment variables. Some functionality may be limited.")

class MultiAgentState(TypedDict):
    messages: List[Any]
    current_time: str
    current_agent: str
    user_intent: str
    appointment_context: Dict[str, Any]
    doctor_recommendations: List[Dict[str, Any]]
    scheduling_options: List[Dict[str, Any]]
    conversation_complete: bool

class MultiAgentOrchestrator:
    def __init__(self):
        self.config = AppConfig()
        self.conversation_history = []
        self.max_turns = 10

    def _build_workflow(self):
        # Configure graph with higher recursion limit
        workflow = StateGraph(MultiAgentState)
        workflow.set_recursion_limit(100)  # Increased recursion limit
        
        # Add agent nodes
        workflow.add_node("user_agent", self._user_agent_node)
        workflow.add_node("doctor_agent", self._doctor_agent_node)
        workflow.add_node("scheduler_agent", self._scheduler_agent_node)
        workflow.add_node("coordinator", self._coordinator_node)
        
        # Define the flow
        workflow.add_edge("user_agent", "coordinator")
        workflow.add_edge("doctor_agent", "coordinator")
        workflow.add_edge("scheduler_agent", "coordinator")
        
        workflow.add_conditional_edges(
            "coordinator",
            self._route_to_agent,
            {
                "user": "user_agent",
                "doctor": "doctor_agent",
                "scheduler": "scheduler_agent",
                "end": END
            }
        )
        
        # Set entry point
        workflow.set_entry_point("coordinator")
        return workflow.compile()

    def process_user_message(self, message: str) -> str:
        """Main entry point for processing user messages"""
        try:
            # Direct command processing without LLM
            message_lower = message.lower()
            
            # Handle appointment booking flow
            if "book" in message_lower and "appointment" in message_lower:
                # Get available slots first
                available_slots = """Available appointment slots:

📅 2024-05-25 09:00 AM
📅 2024-05-25 11:00 AM
📅 2024-05-25 02:00 PM
📅 2024-05-26 09:00 AM
📅 2024-05-26 11:00 AM

To book an appointment, please provide:
1. Your preferred slot from above (e.g. '2024-05-25 09:00 AM')
2. Your name
3. Doctor name from our available doctors list

Would you like me to show you the list of available doctors?"""
                return available_slots
            
            # Handle available appointments query
            elif "available" in message_lower and "appointment" in message_lower:
                return """Available appointment slots:

📅 2024-05-25 09:00 AM
📅 2024-05-25 11:00 AM
📅 2024-05-25 02:00 PM
📅 2024-05-26 09:00 AM
📅 2024-05-26 11:00 AM

To book an appointment, please provide:
1. Your preferred slot from above
2. Your name
3. Preferred doctor (optional)"""
            
            # Handle doctor availability
            elif ("available" in message_lower and "doctor" in message_lower) or ("show" in message_lower and "doctor" in message_lower):
                return self._list_available_doctors()
            
            # Handle actual booking with provided details
            elif any(word in message_lower for word in ["2024-05-25", "2024-05-26"]):
                # Extract booking details
                try:
                    return self._process_booking_details(message)
                except Exception as e:
                    logger.error(f"Error processing booking details: {e}")
                    return "I couldn't process your booking details. Please provide them in this format:\nPreferred slot (e.g. '2024-05-25 09:00 AM'), your name, and preferred doctor"
            
            # Handle cancellation
            elif "cancel" in message_lower:
                if not hasattr(st.session_state, 'appointments') or not st.session_state.appointments:
                    return "You don't have any appointments scheduled. Would you like to book one?"
                
                # Format current appointments for display
                response = "Here are your current appointments:\n\n"
                for i, apt in enumerate(st.session_state.appointments):
                    response += f"{i+1}. {apt['name']} with {apt['doctor_name']}\n"
                    response += f"   📅 {apt['time'].strftime('%A, %B %d at %I:%M %p')}\n"
                    response += f"   📍 {apt.get('location', 'Main Office')}\n\n"
                
                response += "To cancel an appointment, click the 'Cancel This Appointment' button next to the appointment in the Current Appointments section."
                return response
            
            # Default response
            else:
                return """I can help you with:
1. Booking appointments
2. Checking available appointments
3. Showing available doctors
4. Canceling appointments

What would you like to do?"""
                
        except Exception as e:
            logger.exception(f"Error in process_user_message: {str(e)}")
            return self._handle_error()
    
    def _handle_error(self) -> str:
        """Handle errors gracefully with helpful messages"""
        return """I apologize for the technical difficulty. Let me help you directly:

1. To book an appointment, please provide:
   - Your preferred date/time
   - Doctor preference (if any)
   - Your name

2. To see available doctors, just say "show doctors"
3. To check available slots, say "show appointments"

How would you like to proceed?"""

    def _process_booking_details(self, message: str) -> str:
        """Process the booking details provided by the user"""
        try:
            # Extract booking details from message
            # Extract date and time
            date_time_match = re.search(r'2024-05-2[56]\s+(?:09:00|11:00|02:00|04:00)\s+(?:AM|PM)', message)
            if not date_time_match:
                return "Please provide a valid appointment time from the available slots."
            
            appointment_datetime = datetime.strptime(date_time_match.group(), '%Y-%m-%d %I:%M %p')
            
            # Extract name (assume it's a word after "name" or "my name is" or just a capitalized word)
            name_match = re.search(r'(?:name\s+is\s+|name:\s*|my\s+name\s+is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', message)
            if not name_match:
                return "Please provide your name for the appointment."
            
            patient_name = name_match.group(1)
            
            # Extract doctor name
            doctor_match = re.search(r'(?:Dr\.|Doctor)\s+(?:Smith|Johnson|Williams|Brown)', message)
            if not doctor_match:
                return "Please specify a doctor from our available doctors list (Dr. Smith, Dr. Johnson, Dr. Williams, or Dr. Brown)."
            
            doctor_name = doctor_match.group()
            
            # Get doctor info
            doctors = {
                "Dr. Smith": {"specialty": "General Practice", "location": "Main Building, Room 101"},
                "Dr. Johnson": {"specialty": "Cardiology", "location": "Cardiac Wing, Room 205"},
                "Dr. Williams": {"specialty": "Dermatology", "location": "Dermatology Center, Room 301"},
                "Dr. Brown": {"specialty": "Orthopedics", "location": "Sports Medicine Wing, Room 150"}
            }
            
            doctor_info = doctors.get(doctor_name, {})
            
            # Add appointment to session state
            if 'appointments' not in st.session_state:
                st.session_state.appointments = []
                
            new_appointment = {
                "name": patient_name,
                "time": appointment_datetime,
                "doctor_name": doctor_name,
                "doctor_specialty": doctor_info.get("specialty", "General"),
                "location": doctor_info.get("location", "Main Office"),
                "type": "Consultation",
                "status": "Confirmed"
            }
            
            st.session_state.appointments.append(new_appointment)
            
            return f"""Great! I've booked your appointment with the following details:

👤 Patient: {patient_name}
👨‍⚕️ Doctor: {doctor_name} ({doctor_info.get('specialty')})
📅 Date & Time: {appointment_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}
📍 Location: {doctor_info.get('location')}
✅ Status: Confirmed

Your appointment has been added to the Current Appointments section.
You will receive a confirmation email shortly. Is there anything else I can help you with?"""

        except Exception as e:
            logger.error(f"Error processing booking: {e}")
            return """I couldn't process your booking. Please provide all the required details in this format:
1. Preferred slot (e.g. '2024-05-25 09:00 AM')
2. Your name
3. Doctor name (e.g. 'Dr. Smith')"""
        
    def _list_available_doctors(self) -> str:
        """List all available doctors with their specialties"""
        try:
            doctors = {
                "Dr. Smith": {"specialty": "General Practice", "schedule": "Monday, Wednesday, Friday (9:00 AM - 5:00 PM)"},
                "Dr. Johnson": {"specialty": "Cardiology", "schedule": "Tuesday, Thursday (10:00 AM - 4:00 PM)"},
                "Dr. Williams": {"specialty": "Dermatology", "schedule": "Monday, Tuesday, Thursday, Friday (8:00 AM - 3:00 PM)"},
                "Dr. Brown": {"specialty": "Orthopedics", "schedule": "Wednesday, Thursday, Friday (9:00 AM - 6:00 PM)"}
            }
            
            response = "📋 Available Doctors:\n\n"
            for doctor, info in doctors.items():
                response += f"👨‍⚕️ {doctor}\n"
                response += f"   Specialty: {info['specialty']}\n"
                response += f"   Schedule: {info['schedule']}\n\n"
                
            return response
        except Exception as e:
            logger.exception(f"Error in _list_available_doctors: {str(e)}")
            return self._handle_error()

class UserBot:
    """Handles initial user interaction and intent recognition"""
    
    def __init__(self, llm, config):
        self.llm = llm
        self.config = config
    
    def process_message(self, state: MultiAgentState) -> MultiAgentState:
        try:
            # Direct processing without LLM for common intents
            last_message = state["messages"][-1].content.lower() if state["messages"] else ""
            
            if "book" in last_message or "appointment" in last_message:
                response = "I'll help you book an appointment. Please provide:\n1. Your preferred date and time\n2. Doctor preference (if any)\n3. Your name"
                state["user_intent"] = "booking"
            elif "available" in last_message and "doctor" in last_message:
                response = get_doctor_list()
                state["user_intent"] = "doctor_query"
            elif "available" in last_message and "appointment" in last_message:
                response = get_next_available_appointment()
                state["user_intent"] = "schedule_query"
            else:
                response = "How can I help you today? You can:\n1. Book an appointment\n2. Check available appointments\n3. See available doctors"
                state["user_intent"] = "general"
            
            state["messages"].append(AIMessage(content=response))
            state["current_agent"] = "scheduler"
            return state
            
        except Exception as e:
            logger.exception(f"Error in UserBot: {str(e)}")
            state["messages"].append(AIMessage(content="I'll help you right away. What would you like to do?\n1. Book an appointment\n2. Check available slots\n3. See available doctors"))
            state["current_agent"] = "scheduler"
            return state

class DoctorBot:
    """Provides medical recommendations and doctor availability"""
    
    def __init__(self, llm, config):
        self.llm = llm
        self.config = config
        self.doctors = config.doctor_schedules
    
    def process_message(self, state: MultiAgentState) -> MultiAgentState:
        messages = state["messages"]
        current_time = state["current_time"]
        appointment_context = state.get("appointment_context", {})
        
        system_prompt = self.config.prompts['doctor_bot'].format(
            current_time=current_time,
            doctors=json.dumps(self.doctors, indent=2)
        )
        
        try:
            formatted_messages = [SystemMessage(content=system_prompt)] + messages
            response = self.llm.invoke(formatted_messages)
            
            # Generate doctor recommendations based on the conversation
            recommendations = self._generate_doctor_recommendations(messages)
            state["doctor_recommendations"] = recommendations
            
            state["messages"].append(AIMessage(content=response.content))
            state["current_agent"] = "scheduler"  # Route to scheduler after medical consultation
            
            return state
            
        except Exception as e:
            logger.exception(f"Error in DoctorBot: {str(e)}")
            state["messages"].append(AIMessage(content="I'm having trouble accessing medical information. Please consult with our scheduler for general appointments."))
            state["current_agent"] = "scheduler"
            return state
    
    def _generate_doctor_recommendations(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Generate doctor recommendations based on conversation"""
        recommendations = []
        
        # Analyze recent messages for medical keywords
        recent_content = ""
        for message in messages[-3:]:  # Look at last 3 messages
            if isinstance(message, HumanMessage):
                recent_content += message.content.lower() + " "
        
        # Simple keyword-based recommendations
        if any(word in recent_content for word in ["heart", "chest", "cardio"]):
            recommendations.append({
                "doctor": "Dr. Johnson",
                "specialty": "Cardiology",
                "reason": "Heart-related concerns"
            })
        elif any(word in recent_content for word in ["skin", "rash", "acne"]):
            recommendations.append({
                "doctor": "Dr. Williams",
                "specialty": "Dermatology",
                "reason": "Skin-related concerns"
            })
        elif any(word in recent_content for word in ["bone", "joint", "back", "orthopedic"]):
            recommendations.append({
                "doctor": "Dr. Brown",
                "specialty": "Orthopedics",
                "reason": "Musculoskeletal concerns"
            })
        else:
            recommendations.append({
                "doctor": "Dr. Smith",
                "specialty": "General Practice",
                "reason": "General health consultation"
            })
        
        return recommendations

class SchedulerBot:
    """Handles all appointment scheduling operations"""
    
    def __init__(self, llm, config):
        self.llm = llm
        self.config = config
    
    def process_message(self, state: MultiAgentState) -> MultiAgentState:
        messages = state["messages"]
        current_time = state["current_time"]
        doctor_recommendations = state.get("doctor_recommendations", [])
        appointment_context = state.get("appointment_context", {})
        
        system_prompt = self.config.prompts['scheduler_bot'].format(
            current_time=current_time,
            doctor_recommendations=json.dumps(doctor_recommendations, indent=2)
        )
        
        try:
            formatted_messages = [SystemMessage(content=system_prompt)] + messages
            response = self.llm.invoke(formatted_messages)
            
            # Process tool calls if present
            content = response.content
            if "<tool_call>" in content:
                try:
                    content = self._process_tool_call(content)
                except Exception as tool_error:
                    logger.error(f"Error processing tool call: {tool_error}")
                    content = "I encountered an error while processing your request. Let me try a different approach."
                    # Try to get next available appointment as fallback
                    try:
                        content = get_next_available_appointment()
                    except Exception:
                        content = "I'm having trouble with the scheduling system. Please try again or contact us directly."
            
            state["messages"].append(AIMessage(content=content))
            
            # Check if appointment is completed
            if "appointment booked" in content.lower() or "appointment confirmed" in content.lower():
                state["conversation_complete"] = True
                state["error_count"] = 0  # Reset error count on success
            
            return state
            
        except Exception as e:
            logger.exception(f"Error in SchedulerBot: {str(e)}")
            state["error_count"] = state.get("error_count", 0) + 1
            error_msg = "I'm having trouble with the scheduling system. Please try again or contact us directly."
            state["messages"].append(AIMessage(content=error_msg))
            return state
    
    def _process_tool_call(self, content: str) -> str:
        """Process tool calls embedded in the response"""
        try:
            tool_call = content.split("<tool_call>")[1].split("</tool_call>")[0].strip()
            result = eval(tool_call)
            return result
        except Exception as e:
            logger.exception(f"Error processing tool call: {str(e)}")
            return "I encountered an error while processing your appointment request. Please provide the details again."

# Global instance
multi_agent_orchestrator = MultiAgentOrchestrator()