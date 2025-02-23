import os
import requests
from dotenv import load_dotenv
import PyPDF2

# Load environment variables
load_dotenv(override=True)

# Groq API configuration
API_KEY = os.getenv("GROQ_TOKEN")  # Ensure this is correctly set
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# Function to extract text from a PDF resume
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

# Example Usage
if __name__ == "__main__":
    # Path to the resume PDF
    
    resume_path = "ammar-resume.pdf"  
    resume_text = extract_text_from_pdf(resume_path)
    print("Extracted Resume Text:\n", resume_text)

    # Step 2: Analyze the resume
    analysis_result = analyze_resume(resume_text)
    print("\nResume Analysis:\n", analysis_result)