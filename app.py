from logic import run_genai_logic_audio, route_based_on_classification
import google.generativeai as genai
from dotenv import load_dotenv
import moviepy.editor as mp
import numpy as np
import cv2
import pyautogui
import pyaudio
import wave
import os
import time
import threading
import keyboard
import streamlit as st
import pygetwindow as gw  # For getting window information
from pywinauto.application import Application  # For controlling the window

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

def record_screen(filename, stop_event):
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, 8, (screen_size.width, screen_size.height))

    while not stop_event.is_set():
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()

def combine_and_cleanup(video_filename, audio_filename, final_filename):
    video_clip = mp.VideoFileClip(video_filename)
    audio_clip = mp.AudioFileClip(audio_filename)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(final_filename, codec='libx264')

def minimize_browser():
    # Find the active browser window
    browser_window = None
    for window in gw.getAllTitles():
        if "chrome" in window.lower() or "firefox" in window.lower() or "edge" in window.lower():
            browser_window = window
            break

    if browser_window:
        # Connect to the browser window and minimize it
        app = Application().connect(title_re=browser_window)
        app.window(title_re=browser_window).minimize()
    else:
        print("Browser window not found.")

def main():
    stop_event = threading.Event()
    st.title("T.A.P.A.S - Technical Assistance Platform for Advanced Solution")
    
    # Create two columns for the buttons
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button("Start")
    with col2:
        stop_button = st.button("Stop")
    
    if start_button:
        minimize_browser()  # Minimize the browser when the start button is pressed
        
        # Cleanup old files before starting a new session
        cleanup_files()
        
        # Start audio and screen recording in separate threads
        audio_thread = threading.Thread(target=record_audio, args=(audio_filename, stop_event))
        screen_thread = threading.Thread(target=record_screen, args=(video_filename, stop_event))
        
        audio_thread.start()
        screen_thread.start()
        
        st.write("Recording started. Press 'q' or click 'Stop Recording' to stop.")
        
        # Wait for 'q' key press or stop button click to stop recording
        while True:
            if keyboard.is_pressed('q') or stop_button:
                stop_event.set()
                break
        
        audio_thread.join()
        screen_thread.join()
        
        # Ensure files were created
        if not os.path.exists(audio_filename):
            st.error("Audio file was not created!")
            return
        if not os.path.exists(video_filename):
            st.error("Video file was not created!")
            return
        
        # Combine the audio and video files after recording stops
        combine_and_cleanup(video_filename, audio_filename, final_filename)
        st.success("Your output is generating.")
        transcribed_text = run_genai_logic_audio(audio_filename)
        result = route_based_on_classification(transcribed_text, video_filename)
        st.markdown(result)
        
        # Cleanup old files after completion
        cleanup_files()

if __name__ == "__main__":
    main()
