import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def run_genai_logic_audio(audio_file):
    my_audio_file = genai.upload_file(path = "C:/Users/Dalbir Singh/OneDrive/Documents/Major Project/LUMIS/output.wav")
    prompt = "Answer the question asked in audio"
    response = model.generate_content([my_audio_file, prompt])
    return response.text

def run_genai_logic(video_file):
    prompt = '''
    Your task is to extract detailed information from everything visible in the screen recording , Propose solutions only in response to errors or specific questions asked in the audio. Ensure accuracy and clarity in your analysis.
    '''
    myfile = genai.upload_file(path = "C:/Users/Dalbir Singh/OneDrive/Documents/Major Project/LUMIS/final_output.mp4")

    while myfile.state.name == "PROCESSING":
        time.sleep(5)
        myfile = genai.get_file(myfile.name)

    result = model.generate_content([myfile, prompt])
    result = result.text

    finetune_prompt = f'''Present the {result} concisely, clearly, and accurately. As an expert assistant, give a brief but comprehensive explanation that highlights key details and insights. Ensure the explanation is easy to understand, making the data's implications clear and actionable..'''

    final_result = model.generate_content([finetune_prompt])
    return final_result.text
