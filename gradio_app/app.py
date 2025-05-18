import os
import tempfile
import requests
import gradio as gr
import scipy.io.wavfile
import time
import logging
from datetime import datetime

# CODE

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('voice_chatbot_frontend')

API_URL = "http://localhost:8000/voice-chat"
REQUEST_TIMEOUT = 300  # Timeout in seconds

# Voice chat function with improved error handling


def voice_chat(audio, progress=gr.Progress()):
    if audio is None:
        return None, "⚠️ Mohon rekam suara terlebih dahulu"

    # Update timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.info(f"Processing voice request at {timestamp}")

    # Add progress updates
    progress(0, desc="Memproses suara...")

    try:
        sr, audio_data = audio

        # Log audio details for debugging
        logger.info(f"Audio sample rate: {sr}, shape: {audio_data.shape}")

        # Save as .wav with unique filename
        audio_filename = f"input_{int(time.time())}.wav"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)

        scipy.io.wavfile.write(audio_path, sr, audio_data)
        logger.info(f"Saved input audio to: {audio_path}")

        if not os.path.exists(audio_path):
            logger.error(f"Failed to save audio file at {audio_path}")
            return None, "⚠️ Gagal menyimpan file audio"

        progress(0.3, desc="Mengirim ke server...")

        # Send to FastAPI endpoint with timeout
        try:
            logger.info(f"Sending request to {API_URL}")
            with open(audio_path, "rb") as f:
                files = {"file": (audio_filename, f, "audio/wav")}
                response = requests.post(
                    API_URL,
                    files=files,
                    timeout=REQUEST_TIMEOUT
                )

            logger.info(
                f"Response status: {response.status_code}, Content length: {len(response.content) if response.content else 0}")

        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            error_msg = "🕒 Waktu permintaan habis. Server membutuhkan waktu terlalu lama untuk merespons."
            return None, error_msg

        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            error_msg = "🔌 Tidak dapat terhubung ke server. Pastikan server berjalan di http://localhost:8000"
            return None, error_msg

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            error_msg = f"🔴 Error: {str(e)}"
            return None, error_msg

        progress(0.7, desc="Mendapatkan balasan...")

        if response.status_code == 200:
            logger.info("Request successful, processing response")

            # Verify content type and length
            content_type = response.headers.get('Content-Type', '')
            logger.info(f"Response Content-Type: {content_type}")

            if not response.content:
                logger.error("Response content is empty")
                error_msg = "⚠️ Server mengembalikan respons kosong"
                return None, error_msg

            # Save response audio with unique timestamp to avoid caching issues
            output_audio_path = os.path.join(
                tempfile.gettempdir(), f"tts_output_{int(time.time())}.wav")

            try:
                with open(output_audio_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Saved response audio to: {output_audio_path}")

                # Verify if file exists and has content
                if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                    logger.error(
                        f"Output file doesn't exist or is empty: {output_audio_path}")
                    error_msg = "⚠️ File audio respons kosong atau tidak valid"
                    return None, error_msg

            except Exception as e:
                logger.error(f"Failed to save response audio: {e}")
                error_msg = f"⚠️ Gagal menyimpan file audio respons: {str(e)}"
                return None, error_msg

            progress(1.0, desc="Selesai!")
            return output_audio_path, "✅ Berhasil mendapatkan respons"
        else:
            logger.error(
                f"Server returned error status: {response.status_code}")
            try:
                error_content = response.json() if response.content else {}
                error_detail = error_content.get(
                    'message', f"Kode status: {response.status_code}")
            except:
                error_detail = f"Kode status: {response.status_code}"

            error_msg = f"⚠️ Server Error: {error_detail}"
            return None, error_msg

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        error_msg = f"⚠️ Terjadi kesalahan: {str(e)}"
        return None, error_msg


# Dark Green Bottle Theme CSS
custom_css = """
body {
    font-family: 'Poppins', 'Segoe UI', Roboto, Arial, sans-serif;
    background-color: #0a3622;
    color: #e0e0e0;
    margin: 0;
    padding: 0;
    line-height: 1.5;
}

.gradio-container {
    max-width: 1000px !important;
    margin: 0 auto;
}

/* Header Styling */
.header {
    background-color: #072a1b;
    padding: 2rem;
    border-radius: 0 0 20px 20px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    border-bottom: 3px solid #11754a;
}

.app-logo {
    width: 100px;
    height: 100px;
    margin: 0 auto 1rem;
    background-color: #11754a;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.app-title {
    margin: 0;
    font-size: 3rem;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    letter-spacing: 2px;
}

.app-subtitle {
    color: #11cc7c;
    font-size: 1.2rem;
    margin-top: 10px;
    font-weight: 400;
}

/* Panel styling */
.panel {
    background-color: #0d432a;
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    border: 1px solid #11754a;
}

.panel-header {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #11754a;
    padding-bottom: 1rem;
}

.panel-icon {
    margin-right: 12px;
    font-size: 1.5rem;
    color: #11cc7c;
}

.panel-title {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 600;
    color: #ffffff;
}

/* Recording indicator */
.recording-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 12px;
    background-color: #072a1b;
    border: 1px solid #11754a;
}

.pulse-recording {
    display: flex;
    align-items: center;
    color: #ff5252;
    font-weight: 600;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.6; }
    100% { opacity: 1; }
}

.record-icon {
    margin-right: 10px;
    font-size: 1.2rem;
}

/* Status message */
.status-message {
    margin-top: 15px;
    padding: 12px;
    border-radius: 10px;
    text-align: center;
    font-weight: 500;
    font-size: 0.95rem;
}

.status-error {
    background-color: rgba(198, 40, 40, 0.2);
    color: #ff5252;
    border-left: 3px solid #c62828;
}

.status-success {
    background-color: rgba(46, 125, 50, 0.2);
    color: #69f0ae;
    border-left: 3px solid #2e7d32;
}

.status-warning {
    background-color: rgba(249, 168, 37, 0.2);
    color: #ffcc80;
    border-left: 3px solid #f9a825;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1.5rem;
    color: #11cc7c;
    background-color: #072a1b;
    border-radius: 20px 20px 0 0;
    border-top: 3px solid #11754a;
}

.footer a {
    color: #69f0ae;
    text-decoration: none;
}

.footer a:hover {
    text-decoration: underline;
}

/* Wave Animation */
.wave-container {
    height: 60px;
    position: relative;
    margin: 1rem 0;
    overflow: hidden;
    border-radius: 8px;
    background-color: #072a1b;
}

.wave {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.wave-bar {
    background: #11cc7c;
    height: 30%;
    width: 3%;
    margin: 0 1px;
    border-radius: 3px;
    animation: wave 1.2s infinite ease-in-out;
}

.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave {
    0%, 100% { height: 15%; }
    50% { height: 70%; }
}

/* Custom Buttons */
.custom-btn {
    background-color: #11754a;
    border: none;
    color: white;
    padding: 12px 24px;
    border-radius: 50px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
}

.custom-btn:hover {
    background-color: #11cc7c;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
}

.custom-btn:active {
    transform: translateY(1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.btn-icon {
    margin-right: 8px;
}

/* Override Gradio elements */
.gradio-container {
    background-color: #0a3622 !important;
}

button.primary {
    background-color: #11754a !important;
    color: white !important;
}

button.primary:hover {
    background-color: #11cc7c !important;
}

input, textarea, select {
    background-color: #072a1b !important;
    border: 1px solid #11754a !important;
    color: #e0e0e0 !important;
}

input:focus, textarea:focus, select:focus {
    border-color: #11cc7c !important;
    box-shadow: 0 0 0 3px rgba(17, 204, 124, 0.3) !important;
}

.gr-box, .gr-form, .gr-panel {
    background-color: #0d432a !important;
    border-color: #11754a !important;
}

.gr-block {
    border-color: #11754a !important;
}

/* Responsive */
@media (max-width: 768px) {
    .app-title {
        font-size: 2rem;
    }
    
    .panel {
        padding: 1rem;
    }
    
    .app-logo {
        width: 80px;
        height: 80px;
        font-size: 2rem;
    }
    
    .custom-btn {
        padding: 10px 18px;
    }
}
"""

# Create a simpler theme compatible with older Gradio versions
theme = gr.themes.Base(
    primary_hue="green",
    secondary_hue="green",
    neutral_hue="gray"
)

# We'll rely more on custom CSS than the theme API since some properties
# might not be available in your Gradio version

# Recording indicator state function


def recording_state(recording=False):
    if recording:
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)

# Create wave animation HTML


def get_wave_animation():
    return """
    <div class="wave-container">
        <div class="wave">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
        </div>
    </div>
    """


# UI with Gradio Blocks - Dark Green Bottle Theme
with gr.Blocks(theme=theme, css=custom_css) as demo:
    # Header with logo
    gr.HTML("""
    <div class="header">
        <div class="app-logo">🎙️</div>
        <h1 class="app-title">SUARA</h1>
        <p class="app-subtitle">Asisten Suara Bahasa Indonesia</p>
    </div>
    """)

    # Main content area
    with gr.Row():
        # Input Panel
        with gr.Column():
            with gr.Group(elem_classes="panel"):
                gr.HTML("""
                <div class="panel-header">
                    <div class="panel-icon">🎤</div>
                    <h2 class="panel-title">Rekam Suara Anda</h2>
                </div>
                """)

                # Recording indicators
                with gr.Group(elem_classes="recording-indicator"):
                    ready_indicator = gr.HTML("""
                    <div>
                        <span class="record-icon">⚪</span> Siap merekam
                    </div>
                    """, visible=True)

                    recording_active = gr.HTML("""
                    <div class="pulse-recording">
                        <span class="record-icon">🔴</span> Sedang merekam...
                    </div>
                    """, visible=False)

                # Audio input with microphone
                audio_input = gr.Audio(
                    sources="microphone",
                    type="numpy",
                    elem_id="voice-input",
                    streaming=False
                )

                # Wave animation
                gr.HTML(get_wave_animation())

                # Send button
                submit_btn = gr.Button(
                    "🚀 Kirim Pesan Suara",
                    variant="primary",
                    elem_classes="custom-btn"
                )

                # Status message display
                status_msg = gr.HTML(
                    """<div class="status-message">Siap menerima pertanyaan Anda</div>"""
                )

            # Response Panel
            with gr.Group(elem_classes="panel"):
                gr.HTML("""
                <div class="panel-header">
                    <div class="panel-icon">🔊</div>
                    <h2 class="panel-title">Balasan Asisten</h2>
                </div>
                """)

                # Audio output
                audio_output = gr.Audio(
                    type="filepath",
                    elem_id="voice-output",
                    show_label=False
                )

    # Footer with branding
    gr.HTML("""
    <div class="footer">
        <p>SUARA AI © 2025 - Platform AI Berbasis Suara Bahasa Indonesia</p>
        <p>Dibuat dengan 💚 untuk Indonesia</p>
    </div>
    """)

    # Define event handlers
    def update_status(message, is_error=False, is_warning=False):
        if is_error:
            return f'<div class="status-message status-error">{message}</div>'
        elif is_warning:
            return f'<div class="status-message status-warning">{message}</div>'
        else:
            return f'<div class="status-message status-success">{message}</div>'

    # Recording start event
    audio_input.start_recording(
        fn=lambda: recording_state(True),
        outputs=[recording_active, ready_indicator]
    )

    # Recording stop event
    audio_input.stop_recording(
        fn=lambda: recording_state(False),
        outputs=[recording_active, ready_indicator]
    )

    # Submit button click
    submit_btn.click(
        fn=voice_chat,
        inputs=[audio_input],
        outputs=[audio_output, status_msg]
    )

# Launch the app
if __name__ == "__main__":
    logger.info("Starting Voice Chatbot Frontend with Bottle Green Theme")
    demo.launch()
