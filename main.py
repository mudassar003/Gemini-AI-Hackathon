import streamlit as st
import PyPDF2
import os
import json
import google.generativeai as genai
import requests  # For loading animations
from streamlit_lottie import st_lottie
from dotenv import load_dotenv

# ------------------------ API KEY SETUP ------------------------
load_dotenv(".env")
fetched_api_key = os.getenv("API_KEY")
genai.configure(api_key=fetched_api_key)
model = genai.GenerativeModel("gemini-pro")  # Adapt model name if needed
chat = model.start_chat()

# ------------------------ HELPER FUNCTIONS ------------------------
def process_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

def load_lottie_url(url):
    """Loads a Lottie animation from a URL or a local JSON file."""
    with open("Animation.json", 'r') as f:  # Load your local JSON file
        return json.load(f)

def user_input(text, prompt=None):
    """Sends text to the Gemini model, optionally with a prompt."""
    if prompt:
        text = prompt + " " + text
    response = chat.send_message(text, stream=True)
    return response

# ------------------------ STREAMLIT APP ------------------------
# Title and Description
st.title("AI Chatbot with PDF Question Answering & Summarization")
st.write("Upload a PDF research paper to ask questions or get a summary.")

# PDF Upload
uploaded_file = st.file_uploader("Upload a PDF", type=['pdf'])

# Summary Options
st.write("**Summary Options**")
SUMMARY_PROMPTS = [
    "Provide a concise summary of the research paper.",
    "What are the main findings of this paper?",
    "Summarize the key contributions and limitations of this research."
]

# Main Interaction Logic
if uploaded_file:
    pdf_text = process_pdf(uploaded_file)

    st.subheader("Ask Questions or Get a Summary")

    # Input and Summary Options
    user_input_type = st.selectbox("Choose input type", ["Question", "Summary Prompt"])
    if user_input_type == "Question":
        user_quest = st.text_input('Enter your question:')
    else:  # Summary Prompt
        summary_prompt = st.selectbox("Select a summary prompt", SUMMARY_PROMPTS)

    # Response Generation (Conditional)
    if user_input_type == "Question" and user_quest:  # Check both conditions
        try: 
            with st.spinner("Generating response..."):
                result = user_input(pdf_text)  
                st.subheader("Response:")
                for word in result:
                    st.text(word.text)
        except ValueError as e:
            for candidate in result.candidates: 
                if candidate.safety_ratings:
                    st.warning("Response may have been blocked due to safety concerns. Safety Ratings:")
                    st.write(candidate.safety_ratings)
                else:
                    st.error("Error obtaining response text. Please check your API key and network connection.") 

    elif user_input_type == "Summary Prompt":
        try:
            with st.spinner("Generating response..."):
                result = user_input(pdf_text, prompt=summary_prompt)
                st.subheader("Response:")
                for word in result:
                    st.text(word.text)
        except ValueError as e:
            for candidate in result.candidates: 
                if candidate.safety_ratings:
                    st.warning("Response may have been blocked due to safety concerns. Safety Ratings:")
                    st.write(candidate.safety_ratings)
                else:
                    st.error("Error obtaining response text. Please check your API key and network connection.") 


