import streamlit as st
from PyPDF2 import PdfReader
import pdfplumber
from dotenv import load_dotenv
import google.generativeai as genai
from uuid import uuid4
import io

# Initialize and configure the environment
load_dotenv(".env")
fetched_api_key = io.open(".env").read() 
genai.configure(api_key=fetched_api_key)
model = genai.GenerativeModel("gemini-pro")  # Ensure correct model name

def process_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or " ")
    except Exception:
        uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += (page.extract_text() or " ")
        if not text:
            st.error("Failed to extract text from the PDF.")
            return None
    return text

def send_message_to_genai(prompt, history, pdf_text):
    """Sends a message to the Gemini model, including the PDF text only on the first request."""
    if 'chat' not in st.session_state:
        st.session_state.chat = model.start_chat(history=history)

    # Check if the PDF text has already been sent by looking for a flag in the session state
    if 'pdf_sent' not in st.session_state:
        full_prompt = f"{pdf_text}\n{prompt}" if pdf_text else prompt
        st.session_state.pdf_sent = True  # Set a flag indicating the PDF text has been sent
    else:
        full_prompt = prompt

    response = st.session_state.chat.send_message(full_prompt)
    history.append({"role": "user", "content": prompt, "id": str(uuid4())})
    history.append({"role": "model", "content": response.text, "id": str(uuid4())})
    return history

def display_chat_ui(pdf_text):
    """Displays UI components for chat interaction and handles user input."""
    user_input_type = st.radio("Choose input type:", ["Type your question", "Select a summary prompt"], index=0)

    if user_input_type == "Type your question":
        user_input = st.text_input("Enter your question or prompt here:", key="user_input", args=(pdf_text,))
    else:
        SUMMARY_PROMPTS = [
            "Provide a concise summary of the research paper.",
            "What are the main findings of this paper?",
            "Summarize the key contributions and limitations of this research."
        ]
        user_input = st.selectbox("Select a summary prompt:", SUMMARY_PROMPTS, index=0, key="summary_prompt", args=(pdf_text,))

    if st.button("Send") and user_input:
        with st.spinner("Generating response..."):
            st.session_state.chat_history = send_message_to_genai(user_input, st.session_state.chat_history, pdf_text)
            st.rerun()

def display_chat_history():
    """Displays the chat history in a single, non-editable text area."""
    chat_texts = []
    for index, chat in enumerate(st.session_state.chat_history):
        chat_content = str(chat["content"]) if chat["content"] is not None else ""
        prefix = "You: " if chat["role"] == "user" else "Gemini: "
        chat_texts.append(f"{prefix}{chat_content}")

    full_chat_text = "\n".join(chat_texts)
    # Debug print to check the final string type and content
    # print(f"Final chat text type: {type(full_chat_text)}, content: {full_chat_text}")

    # Try using a dynamic key based on session state if static keys might be causing issues
    dynamic_key = f"chat_history_{len(st.session_state.chat_history)}"
    st.text_area("Chat History", value=full_chat_text, height=300, key=dynamic_key, disabled=True)

def main():
    st.title("AI Chatbot with PDF Question Answering & Summarization")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    uploaded_file = st.file_uploader("Upload a PDF", type=['pdf'])
    if uploaded_file:
        pdf_text = process_pdf(uploaded_file)
        if pdf_text:
            st.session_state.pdf_text = pdf_text
            display_chat_history()
            display_chat_ui(pdf_text)

if __name__ == "__main__":
    main()
