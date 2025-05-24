import streamlit as st
import streamlit.components.v1 as components

def audio_recorder():
    """Create an audio recorder interface using HTML5."""
    html = """
    <div style="padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f8f9fa;">
        <div style="margin-bottom: 10px;">
            <button id="startButton" onclick="startRecording()" style="background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">🎤 Start Recording</button>
            <button id="stopButton" onclick="stopRecording()" disabled style="background-color: #f44336; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;">⏹️ Stop Recording</button>
        </div>
        <div id="status" style="margin: 10px 0; font-weight: bold; color: #666;">Not recording</div>
        <div id="transcription" style="margin-top: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; min-height: 50px; background-color: white;"></div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        const status = document.getElementById('status');
        const transcription = document.getElementById('transcription');

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64Audio = reader.result.split(',')[1];
                        window.parent.postMessage({ type: 'audioData', data: base64Audio }, '*');
                        transcription.textContent = 'Processing voice input...';
                        transcription.style.color = '#666';
                    };
                };

                mediaRecorder.start();
                startButton.disabled = true;
                stopButton.disabled = false;
                status.textContent = '🎤 Recording in progress...';
                status.style.color = '#f44336';
                transcription.textContent = 'Recording in progress...';
                transcription.style.color = '#666';
            } catch (err) {
                console.error('Error accessing microphone:', err);
                status.textContent = '❌ Error accessing microphone';
                status.style.color = '#f44336';
                transcription.textContent = 'Error: Could not access microphone. Please check your browser permissions.';
                transcription.style.color = '#f44336';
            }
        }

        function stopRecording() {
            mediaRecorder.stop();
            startButton.disabled = false;
            stopButton.disabled = true;
            status.textContent = '⏳ Processing voice input...';
            status.style.color = '#2196F3';
        }
    </script>
    """
    components.html(html, height=200)

def audio_player(audio_data):
    """Create an audio player for the given base64 audio data."""
    if audio_data:
        html = f"""
        <div style="padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f8f9fa;">
            <audio controls autoplay style="width: 100%;">
                <source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
        components.html(html, height=70) 