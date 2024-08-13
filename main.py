import threading
import os
import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import moviepy.editor as mp
import speech_recognition as sr
import keyboard
import streamlit as st
from genai_logic import run_genai_logic_audio, run_genai_logic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Audio and video file settings
AUDIO_FILE = "output.wav"
AUDIO_FILE_RECORD = "output_1.wav"
VIDEO_FILE = "output.mp4"
FINAL_OUTPUT_FILE = "final_output.mp4"

def record_audio(filename, stop_event):
    print("Starting audio recording...")
    audio = pyaudio.PyAudio()

    try:
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=2048)
    except Exception as e:
        print(f"Error initializing audio stream: {e}")
        return

    frames = []

    while not stop_event.is_set():
        try:
            if stream.is_active():
                data = stream.read(2048)
                frames.append(data)
            else:
                print("Audio stream is not active.")
                break
        except Exception as e:
            print(f"Error recording audio: {e}")
            break

    try:
        stream.stop_stream()
        stream.close()
        audio.terminate()
    except Exception as e:
        print(f"Error closing audio stream: {e}")

    if frames:
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b''.join(frames))
            print(f"Audio recording completed and saved as {filename}.")
        except Exception as e:
            print(f"Error saving audio file: {e}")
    else:
        print("No audio frames captured. Audio file not created.")

def record_screen(filename, stop_event):
    print("Starting screen recording...")
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, 12, (screen_size.width, screen_size.height))

    while not stop_event.is_set():
        img = pyautogui.screenshot()
        frame = np.array(img)
        out.write(frame)

    out.release()
    print(f"Screen recording completed and saved as {filename}.")

def listen_for_commands(start_recording_event, stop_event, audio_only_event, record_switch_event):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while True:
        with microphone as source:
            audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            try:
                text = recognizer.recognize_google(audio_data).lower()
                if "record" in text:
                    print("Record detected. Starting both audio and screen recording.")
                    record_switch_event.set()
                elif "hello" in text:
                    print("Hello detected. Starting audio recording only.")
                    audio_only_event.set()
                elif "cut" in text or "stop" in text:
                    print("Stop detected. Stopping recording.")
                    stop_event.set()
            except sr.UnknownValueError:
                print("Could not understand the audio.")


def delete_old_files():
    for filename in [AUDIO_FILE, AUDIO_FILE_RECORD, VIDEO_FILE, FINAL_OUTPUT_FILE]:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted old file: {filename}")
def app():
    st.set_page_config(page_title="LUMIS", layout="wide")

    # Load CSS from file
    with open("style.css") as f:
        css = f.read()

    # Inject the CSS into the Streamlit app
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.title("LUMIS")

    start_recording_event = threading.Event()
    stop_event = threading.Event()
    audio_only_event = threading.Event()
    record_switch_event = threading.Event()

    # Initialize the list to store previous results
    all_results = []

    # Start listening for commands immediately
    command_thread = threading.Thread(
        target=listen_for_commands,
        args=(start_recording_event, stop_event, audio_only_event, record_switch_event)
    )
    command_thread.daemon = True
    command_thread.start()

    st.write("""Say 'Hello' to start an Audio Search. Say 'Record' to capture both audio and video . Press 'Q' or say 'Stop" to execute the query""")

    # Placeholders for animations and results
    placeholder = st.empty()
    latest_result_placeholder = st.empty()
    previous_outputs_placeholder = st.empty()

    while True:
        # Show Google Voice animation for listening
        with placeholder.container():
            st.markdown(
                '<div class="circle-container">'
                '<div class="voice-circle"></div>'
                '<div class="voice-circle"></div>'
                '<div class="voice-circle"></div>'
                '</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="listening">Listening...</div>', unsafe_allow_html=True)

        # Wait for 'hello' or 'record' command to begin the appropriate recording
        while not (start_recording_event.is_set() or audio_only_event.is_set() or record_switch_event.is_set()):
            if stop_event.is_set() or keyboard.is_pressed('q'):
                stop_event.set()
                break

        # Hide the listening animation once recording starts
        placeholder.empty()

        if audio_only_event.is_set() and not record_switch_event.is_set():
            # Delete old files before starting a new recording
            delete_old_files()

            # Start audio recording only
            audio_thread = threading.Thread(target=record_audio, args=(AUDIO_FILE, stop_event))
            audio_thread.start()

            # Wait for 'stop' command or 'q' key press to stop recording
            while not (stop_event.is_set() or record_switch_event.is_set()):
                if keyboard.is_pressed('q'):
                    stop_event.set()

            audio_thread.join()

            # Confirm that the audio file was created
            if not os.path.exists(AUDIO_FILE):
                raise FileNotFoundError(f"File {AUDIO_FILE} does not exist. Please check the recording process.")

            # Run GenAI logic for audio
            result = run_genai_logic_audio(AUDIO_FILE)

            # Add the latest result to the list of all results
            all_results.append(result)

            # Display the latest result
            latest_result_placeholder.markdown(f'<div class="generated-output">{result}</div>', unsafe_allow_html=True)

            # Display all previous results
            with previous_outputs_placeholder.container():
                for idx, prev_result in enumerate(reversed(all_results[:-1])):
                    st.markdown(f'<div class="previous-output">Previous Result {len(all_results) - idx - 1}: {prev_result}</div>', unsafe_allow_html=True)

            # Reset events
            start_recording_event.clear()
            audio_only_event.clear()
            stop_event.clear()

        elif record_switch_event.is_set():
            # Delete old files before starting a new recording
            delete_old_files()

            # Start both audio and screen recording
            audio_thread = threading.Thread(target=record_audio, args=(AUDIO_FILE_RECORD, stop_event))
            video_thread = threading.Thread(target=record_screen, args=(VIDEO_FILE, stop_event))
            audio_thread.start()
            video_thread.start()

            # Wait for 'stop' command or 'q' key press to stop recording
            while not stop_event.is_set():
                if keyboard.is_pressed('q'):
                    stop_event.set()

            audio_thread.join()
            video_thread.join()

            # Ensure both audio and video files were created
            if not os.path.exists(AUDIO_FILE_RECORD) or not os.path.exists(VIDEO_FILE):
                raise FileNotFoundError("Audio or video files were not created. Please check the recording process.")

            # Combine audio and video
            try:
                audio_clip = mp.AudioFileClip(AUDIO_FILE_RECORD)
                video_clip = mp.VideoFileClip(VIDEO_FILE)
                final_clip = video_clip.set_audio(audio_clip)
                final_clip.write_videofile(FINAL_OUTPUT_FILE, codec="libx264")
                video_file = FINAL_OUTPUT_FILE
            except Exception as e:
                raise Exception(f"Error combining audio and video: {e}")

            # Run GenAI logic for video
            result = run_genai_logic(video_file)

            # Add the latest result to the list of all results
            all_results.append(result)

            # Display the latest result
            latest_result_placeholder.markdown(f'<div class="generated-output">{result}</div>', unsafe_allow_html=True)

            # Display all previous results
            with previous_outputs_placeholder.container():
                for idx, prev_result in enumerate(reversed(all_results[:-1])):
                    st.markdown(f'<div class="previous-output">Result {len(all_results) - idx - 1}: {prev_result}</div>', unsafe_allow_html=True)

            # Reset events
            start_recording_event.clear()
            audio_only_event.clear()
            stop_event.clear()
            record_switch_event.clear()

if __name__ == "__main__":
    app()
