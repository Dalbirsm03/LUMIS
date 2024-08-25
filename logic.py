import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

code_model = genai.GenerativeModel('gemini-1.5-flash')

# Function to transcribe audio
def run_genai_logic_audio(audio_file):
    my_audio_file = genai.upload_file(path=audio_file)
    
    while my_audio_file.state.name == "PROCESSING":
        time.sleep(5)
        my_audio_file = genai.get_file(my_audio_file.name)
    
    prompt = "Understand the audio and convert the audio into text."
    response = code_model.generate_content([my_audio_file, prompt])
    return response.text

# Function to route the task based on code-related classification
def route_based_on_classification(transcribed_text, video_file):
    prompt = f"""
    1. **Explanation of the Error**: Analyze the video '{video_file}' and the spoken issue '{transcribed_text}' to identify the specific problem. Clearly explain the cause of the error.
    2. **Approach to Solve the Error**: Outline the steps needed to resolve the error, focusing on the necessary code changes or adjustments.
    3. **Corrected Code**: Provide the corrected version of the code that addresses the identified issue.
    4. **Summary**: Conclude with a brief summary of the solution, emphasizing the key points and how the changes fix the problem.
    """

    my_video_file = genai.upload_file(path=video_file)
    while my_video_file.state.name == "PROCESSING":
        time.sleep(5)
        my_video_file = genai.get_file(my_video_file.name)
    
    video_response = code_model.generate_content([my_video_file, prompt])
    return video_response.text


audio_file = "output.wav"
video_file = "output.mp4"
