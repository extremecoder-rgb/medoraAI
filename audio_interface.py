import streamlit as st
import streamlit.components.v1 as components

def audio_recorder():
    """Create an audio recorder interface using HTML5."""
    html = """
    <div>
        <button id="startButton" onclick="startRecording()">Start Recording</button>
        <button id="stopButton" onclick="stopRecording()" disabled>Stop Recording</button>
        <div id="status">Not recording</div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        const status = document.getElementById('status');

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
                    };
                };

                mediaRecorder.start();
                startButton.disabled = true;
                stopButton.disabled = false;
                status.textContent = 'Recording...';
            } catch (err) {
                console.error('Error accessing microphone:', err);
                status.textContent = 'Error accessing microphone';
            }
        }

        function stopRecording() {
            mediaRecorder.stop();
            startButton.disabled = false;
            stopButton.disabled = true;
            status.textContent = 'Processing...';
        }
    </script>
    """
    components.html(html, height=100)

def audio_player(audio_data):
    """Create an audio player for the given base64 audio data."""
    if audio_data:
        html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        components.html(html, height=50) 