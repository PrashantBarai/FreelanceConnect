import os
import requests
from dotenv import load_dotenv
import PyPDF2

# Load environment variables
load_dotenv(override=True)


API_KEY = os.getenv("GROQ_TOKEN")  
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to chat with Groq API
def chat_with_llama(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",  # Adjust the model name if needed
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(BASE_URL, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.json()}"

# Function to analyze a resume
def analyze_resume(resume_text):
    prompt = f"""
    Analyze the following resume and provide insights:
    - Key skills
    - Years of experience
    - Education background
    - Suggestions for improvement

    Resume:
    {resume_text}
    """
    return chat_with_llama(prompt)

