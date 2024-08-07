import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

prompt = '''
Your task is to extract detailed information from everything visible in the screen recording,Listen to the audio carefully to capture all spoken words and nuances. Provide a thorough analysis based on both the visual and audio content. Propose solutions only in response to errors or specific questions asked in the audio. Ensure accuracy and clarity in your analysis, presenting findings in a well-structured manner that aligns with the user’s needs and objectives.'''

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
