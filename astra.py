import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import moviepy.editor as mp
import threading
import keyboard
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
import os
import time
load_dotenv()
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
    stream.close()
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

def listen_for_commands(start_recording_event, stop_event):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while not stop_event.is_set():
        with microphone as source:
            print("Listening for commands...")
            audio_data = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio_data).lower()
                print(f"Heard: {text}")

                if "hello" in text:
                    print("Hello detected. Starting recording.")
                    start_recording_event.set()
                elif "stop" in text:
                    print("Stop detected. Stopping recording.")
                    stop_event.set()

            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                print("Could not request results; check your network connection.")

def run_genai_logic(video_file):
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = '''
    Your task is to extract detailed information from everything visible in the screen recording , Propose solutions only in response to errors or specific questions asked in the audio. Ensure accuracy and clarity in your analysis, presenting findings in a well-structured manner that aligns with the user’s needs and objectives.
    "If you encounter any error while recording audio or video, detect the coding language being used and provide a solution in the correct format. As an expert code developer, your response should include whole appropriate code snippet to fix the error.
    '''

    myfile = genai.upload_file(path = "C:/Users/Dalbir Singh/OneDrive/Documents/Major Project/LUMIS/final_output.mp4")

    while myfile.state.name == "PROCESSING":
        time.sleep(5)
        myfile = genai.get_file(myfile.name)

    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content([myfile, prompt])
    result = result.text

    finetune_prompt = f'''Present the {result} concisely, clearly, and accurately. As an expert assistant, give a brief but comprehensive explanation that highlights key details and insights. Ensure the explanation is easy to understand, making the data's implications clear and actionable..'''

    final_result = model.generate_content([finetune_prompt])
    print(final_result.text)

def main():
    start_recording_event = threading.Event()
    stop_event = threading.Event()

    # Start listening for commands
    command_thread = threading.Thread(target=listen_for_commands, args=(start_recording_event, stop_event))
    command_thread.start()

    print("Waiting for 'hello' to start recording and 'stop' or 'q' to stop recording.")

    # Wait for 'hello' to start recording
    start_recording_event.wait()

    # Start audio and screen recording in separate threads
    audio_thread = threading.Thread(target=record_audio, args=(WAVE_OUTPUT_FILENAME, stop_event))
    screen_thread = threading.Thread(target=record_screen, args=(VIDEO_OUTPUT_FILENAME, stop_event))

    audio_thread.start()
    screen_thread.start()

    # Wait for 'stop' command or 'q' key press to stop recording
    while not stop_event.is_set():
        if keyboard.is_pressed('q'):
            print("Key 'q' pressed. Stopping recording.")
            stop_event.set()

    # Ensure both threads have finished
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

    # Run GenAI logic here
    run_genai_logic(final_output_filename)



if __name__ == "__main__":
    main()
