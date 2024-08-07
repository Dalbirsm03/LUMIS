import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import moviepy.editor as mp
import threading
import os
import keyboard  # For key press detection

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "output.wav"
VIDEO_OUTPUT_FILENAME = "output.mp4"

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
    out = cv2.VideoWriter(filename, fourcc, 12.50, (screen_size.width, screen_size.height))

    while not stop_event.is_set():
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()

def main():
    stop_event = threading.Event()

    # Start audio and screen recording in separate threads
    audio_thread = threading.Thread(target=record_audio, args=(WAVE_OUTPUT_FILENAME, stop_event))
    screen_thread = threading.Thread(target=record_screen, args=(VIDEO_OUTPUT_FILENAME, stop_event))

    audio_thread.start()
    screen_thread.start()

    print("Recording started. Press 'q' to stop.")

    # Wait for 'q' key press to stop recording
    while True:
        if keyboard.is_pressed('q'):
            stop_event.set()
            break

    audio_thread.join()
    screen_thread.join()

    # Combine video and audio
    video_clip = mp.VideoFileClip(VIDEO_OUTPUT_FILENAME)
    audio_clip = mp.AudioFileClip(WAVE_OUTPUT_FILENAME)
    video_clip = video_clip.set_audio(audio_clip)

    # Write the result to a file
    final_output_filename = "final_output.mp4"
    video_clip.write_videofile(final_output_filename, codec='libx264')

    # Cleanup temporary files
    os.remove(VIDEO_OUTPUT_FILENAME)
    os.remove(WAVE_OUTPUT_FILENAME)

if __name__ == "__main__":
    main()
