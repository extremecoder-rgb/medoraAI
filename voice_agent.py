import speech_recognition as sr
import pyttsx3
import os
from vosk import Model, KaldiRecognizer
import wave
import json
import tempfile
import sounddevice as sd
import numpy as np
from logger import setup_logger

logger = setup_logger(__name__)

class VoiceAgent:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.setup_voice()
        
        # Initialize Vosk model
        model_path = "vosk-model-small-en-us-0.15"
        if not os.path.exists(model_path):
            logger.warning(f"Vosk model not found at {model_path}. Please download it from https://alphacephei.com/vosk/models")
        else:
            self.vosk_model = Model(model_path)
        
    def setup_voice(self):
        """Configure the text-to-speech engine"""
        voices = self.engine.getProperty('voices')
        # Set a female voice if available
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 150)  # Speed of speech
        
    def text_to_speech(self, text):
        """Convert text to speech"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            logger.debug(f"Text to speech: {text}")
        except Exception as e:
            logger.error(f"Error in text to speech: {str(e)}")
            
    def record_audio(self, duration=5, sample_rate=16000):
        """Record audio from microphone"""
        try:
            logger.info(f"Recording audio for {duration} seconds...")
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            return recording
        except Exception as e:
            logger.error(f"Error recording audio: {str(e)}")
            return None
            
    def save_audio(self, recording, sample_rate=16000):
        """Save recorded audio to a temporary WAV file"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            return temp_file.name
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            return None
            
    def recognize_speech(self, audio_file=None):
        """Recognize speech using Vosk"""
        try:
            if audio_file and os.path.exists(audio_file):
                with wave.open(audio_file, 'rb') as wf:
                    recognizer = KaldiRecognizer(self.vosk_model, wf.getframerate())
                    recognizer.SetWords(True)
                    
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        if recognizer.AcceptWaveform(data):
                            result = json.loads(recognizer.Result())
                            if result.get("text"):
                                logger.debug(f"Recognized text: {result['text']}")
                                return result['text']
                    
                    # Get final result
                    result = json.loads(recognizer.FinalResult())
                    if result.get("text"):
                        logger.debug(f"Final recognized text: {result['text']}")
                        return result['text']
            
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            return None
            
    def process_voice_command(self):
        """Record and process voice command"""
        try:
            # Record audio
            recording = self.record_audio()
            if recording is None:
                return None
                
            # Save to temporary file
            audio_file = self.save_audio(recording)
            if audio_file is None:
                return None
                
            # Recognize speech
            text = self.recognize_speech(audio_file)
            
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
                
            return text
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return None
