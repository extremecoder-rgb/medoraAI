import asyncio
import sounddevice as sd
import numpy as np
import wave
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

logger = setup_logger(__name__)

class VoiceAgent:
    def __init__(self):
        try:
            self.sample_rate = 44100
            self.channels = 1
            self.duration = 5  # seconds
            
            # Initialize pygame mixer only if not already initialized
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except Exception as e:
                    logger.error(f"Failed to initialize pygame mixer: {e}")
                    logger.warning("Text-to-speech functionality will be disabled")
            
            self._loop = None
            self.temp_dir = tempfile.gettempdir()
            self.recognizer = sr.Recognizer()
            self.current_audio_file = None
            
            # Test audio device availability
            try:
                sd.check_input_settings(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.float32
                )
            except Exception as e:
                logger.error(f"Audio input device not available: {e}")
                logger.warning("Voice input functionality will be disabled")
            
            # Adjust for ambient noise
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 500  # Even lower threshold for better sensitivity
            self.recognizer.pause_threshold = 0.2  # Shorter pause threshold
            self.recognizer.phrase_threshold = 0.1  # More sensitive to phrases
            self.recognizer.non_speaking_duration = 0.1  # Shorter non-speaking duration
            
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

    def process_voice_command(self):
        """Process voice command with improved error handling and feedback."""
        try:
            logger.info("Starting voice recording...")
            
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name

            # Record audio with error handling
            try:
                logger.info("Recording audio...")
                recording = sd.rec(
                    int(self.duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='float32'
                )
                sd.wait()
                
                # Check if recording is empty or too quiet
                max_amplitude = np.max(np.abs(recording))
                logger.info(f"Recording max amplitude: {max_amplitude}")
                
                if max_amplitude < 0.001:  # Much lower threshold for better sensitivity
                    logger.warning("Recording too quiet or empty")
                    return "I couldn't hear anything. Please try again."
                
            except Exception as e:
                logger.error(f"Error during audio recording: {str(e)}")
                return "Error recording audio. Please try again."
            
            # Save to WAV file
            try:
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 2 bytes for float32
                    wf.setframerate(self.sample_rate)
                    wf.writeframes((recording * 32767).astype(np.int16).tobytes())
            except Exception as e:
                logger.error(f"Error saving audio file: {str(e)}")
                return "Error saving audio. Please try again."
            
            logger.info("Audio recorded, processing speech...")
            
            # Process the audio file
            try:
                with sr.AudioFile(temp_filename) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Record the audio
                    audio = self.recognizer.record(source)
                    
                    try:
                        # Use Google's speech recognition
                        text = self.recognizer.recognize_google(audio)
                        logger.info(f"Successfully recognized speech: {text}")
                        
                        if not text.strip():
                            logger.warning("Empty speech detected")
                            return "I couldn't hear anything. Please try again."
                        
                        return text
                        
                    except sr.UnknownValueError:
                        logger.warning("Speech not recognized")
                        return "I couldn't understand what you said. Please try again."
                    except sr.RequestError as e:
                        logger.error(f"Speech recognition service error: {str(e)}")
                        return "Sorry, there was an error with the speech recognition service. Please try again."
                    
            except Exception as e:
                logger.error(f"Error processing audio file: {str(e)}")
                return "Error processing audio. Please try again."
                
        except Exception as e:
            logger.error(f"Error in voice processing: {str(e)}")
            return "Sorry, there was an error processing your voice input. Please try again."
        finally:
            # Clean up the temporary file
            try:
                if 'temp_filename' in locals():
                    os.unlink(temp_filename)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

    def text_to_speech(self, text):
        """Convert text to speech with improved error handling."""
        try:
            if not text:
                logger.warning("Empty text provided for text-to-speech")
                return
                
            logger.info(f"Converting text to speech: {text}")
            
            # Create a temporary file with a unique name
            temp_file = os.path.join(self.temp_dir, f"tts_{int(time.time())}.mp3")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file)
            
            # Wait a moment to ensure the file is written
            time.sleep(0.5)
            
            # Play the audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Clean up after playback is complete
            pygame.mixer.music.unload()
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error cleaning up audio file: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in text to speech: {str(e)}")
            # Don't re-raise the exception, just log it
