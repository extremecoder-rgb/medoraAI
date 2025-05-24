import asyncio
import tempfile
import os
from gtts import gTTS
import pygame
from logger import setup_logger
import time
import speech_recognition as sr
import queue
import threading
import sys
import streamlit as st
import base64
import json

logger = setup_logger(__name__)

class VoiceAgent:
    def __init__(self):
        try:
            # Set environment variable to use dummy audio driver
            os.environ['SDL_AUDIODRIVER'] = 'dummy'
            
            # Initialize pygame mixer with dummy driver
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init(devicename='dummy')
                except Exception as e:
                    logger.error(f"Failed to initialize pygame mixer: {e}")
                    logger.warning("Text-to-speech functionality will be disabled")
            
            self._loop = None
            self.temp_dir = tempfile.gettempdir()
            self.recognizer = sr.Recognizer()
            self.current_audio_file = None
            
            # Adjust for ambient noise
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 500  # Even lower threshold for better sensitivity
            self.recognizer.pause_threshold = 0.2  # Shorter pause threshold
            self.recognizer.phrase_threshold = 0.1  # More sensitive to phrases
            self.recognizer.non_speaking_duration = 0.1
            
            # Initialize audio queue
            self.audio_queue = queue.Queue()
            self.is_recording = False
            
            logger.info("VoiceAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VoiceAgent: {e}")
            raise RuntimeError(f"VoiceAgent initialization failed: {e}")

    def _get_event_loop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def process_voice_command(self, audio_data=None):
        """Process voice command from browser audio data."""
        if not audio_data:
            return "No audio data received. Please try again."
        
        try:
            # Convert base64 audio data to temporary file
            audio_bytes = base64.b64decode(audio_data)
            temp_file = os.path.join(self.temp_dir, f"voice_input_{int(time.time())}.wav")
            
            with open(temp_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Use speech recognition to convert audio to text
            with sr.AudioFile(temp_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
            
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error cleaning up audio file: {str(e)}")
            
            return text
                
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return "Sorry, there was an error processing your voice input. Please try again."

    def text_to_speech(self, text):
        """Convert text to speech and return base64 audio data."""
        try:
            if not text:
                logger.warning("Empty text provided for text-to-speech")
                return None
                
            logger.info(f"Converting text to speech: {text}")
            
            # Create a temporary file with a unique name
            temp_file = os.path.join(self.temp_dir, f"tts_{int(time.time())}.mp3")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file)
            
            # Read the file and convert to base64
            with open(temp_file, 'rb') as audio_file:
                audio_data = audio_file.read()
                base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error cleaning up audio file: {str(e)}")
            
            return base64_audio
                
        except Exception as e:
            logger.error(f"Error in text to speech: {str(e)}")
            return None

    def get_audio_html(self, text):
        """Generate HTML for audio playback."""
        audio_data = self.text_to_speech(text)
        if audio_data:
            return f"""
            <audio controls autoplay>
                <source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            """
        return ""
