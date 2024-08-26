import streamlit as st
import os
import threading
import pyautogui
import numpy as np
import cv2
import pyaudio
import wave
import moviepy.editor as mp
import keyboard
from pywinauto.application import Application
import pygetwindow as gw
from logic import run_genai_logic_audio, route_based_on_classification
from dotenv import load_dotenv

load_dotenv()

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

# File paths
audio_filename = "output.wav"
video_filename = "output.mp4"
final_filename = "final_output.mp4"

# Initialize Streamlit
st.set_page_config(page_title="T.A.P.A.S", page_icon=":camera:", layout="wide")
st.title("T.A.P.A.S - Technical Assistance Platform for Advanced Solution")

# Initialize session state for outputs
if 'outputs' not in st.session_state or not isinstance(st.session_state.outputs, dict):
    st.session_state.outputs = {}

if 'current_session' not in st.session_state:
    st.session_state.current_session = 'Session 1'

def cleanup_files():
    """Deletes old files before a new recording session starts."""
    files_to_delete = [audio_filename, video_filename, final_filename]
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted old file: {file}")

def record_audio(filename, stop_event):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    while not stop_event.is_set():
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def record_screen(filename, stop_event, mouse_positions):
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, 8, (screen_size.width, screen_size.height))

    while not stop_event.is_set():
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Capture mouse cursor
        x, y = pyautogui.position()
        cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
        out.write(frame)
        mouse_positions.append((x, y))  # Track mouse positions

    out.release()

def combine_and_cleanup(video_filename, audio_filename, final_filename):
    video_clip = mp.VideoFileClip(video_filename)
    audio_clip = mp.AudioFileClip(audio_filename)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(final_filename, codec='libx264')

def minimize_browser():
    browser_window = None
    for window in gw.getAllTitles():
        if "chrome" in window.lower() or "firefox" in window.lower() or "edge" in window.lower():
            browser_window = window
            break

    if browser_window:
        app = Application().connect(title_re=browser_window)
        app.window(title_re=browser_window).minimize()
    else:
        print("Browser window not found.")

def main():
    stop_event = threading.Event()

    # Sidebar for session selection
    with st.sidebar:
        st.title("Sessions")
        session_name = st.text_input("New Session Name", "")
        if st.button("Start New Session") and session_name:
            st.session_state.current_session = session_name
            st.session_state.outputs[session_name] = []
        session_names = list(st.session_state.outputs.keys())
        if session_names:
            session_selection = st.selectbox("Choose a session", session_names)
            if session_selection:
                st.session_state.current_session = session_selection

    st.header(f"Current Session: {st.session_state.current_session}")

    # Initialize the current session's outputs if it doesn't exist
    if st.session_state.current_session not in st.session_state.outputs:
        st.session_state.outputs[st.session_state.current_session] = []

    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("Start")
    with col2:
        stop_button = st.button("Stop")

    if start_button:
        minimize_browser()
        cleanup_files()

        audio_thread = threading.Thread(target=record_audio, args=(audio_filename, stop_event))
        mouse_positions = []
        screen_thread = threading.Thread(target=record_screen, args=(video_filename, stop_event, mouse_positions))

        audio_thread.start()
        screen_thread.start()

        st.write("Recording started. Press 'q' or click 'Stop' to stop.")

        while True:
            if keyboard.is_pressed('q') or stop_button:
                stop_event.set()
                break

        audio_thread.join()
        screen_thread.join()

        if not os.path.exists(audio_filename):
            st.error("Audio file was not created!")
            return
        if not os.path.exists(video_filename):
            st.error("Video file was not created!")
            return

        combine_and_cleanup(video_filename, audio_filename, final_filename)
        st.success("Your output is generating.")
        transcribed_text = run_genai_logic_audio(audio_filename)

        selected_lines = "Captured code lines based on cursor position and analysis"

        result = route_based_on_classification(transcribed_text, video_filename, selected_lines)

        st.session_state.outputs[st.session_state.current_session].append(result)

    # Display all outputs for the current session
    for output in st.session_state.outputs[st.session_state.current_session]:
        st.markdown(f"""
            <div style="background-color: darkgray; border-radius: 10px; padding: 10px; margin-bottom: 10px;">
                <i class="fas fa-check-circle"></i> {output}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
