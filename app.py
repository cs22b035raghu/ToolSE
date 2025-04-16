import streamlit as st
import fitz  # PyMuPDF
from transformers import pipeline

# Function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Function to summarize text
def summarize_text(text, max_length=200, min_length=50):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)[0]["summary_text"]

# Streamlit UI
st.title("📄 PDF Summarizer")
st.write("Upload a PDF file, and get an AI-generated summary!")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Extract text
    extracted_text = extract_text_from_pdf(uploaded_file)

    if extracted_text:
        # Show extracted text (optional)
        with st.expander("🔍 View Extracted Text"):
            st.write(extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text)

        # Summarize text
        st.write("📌 **Generating Summary...**")
        summary = summarize_text(extracted_text)

        # Display summary
        st.subheader("📝 Summary")
        st.write(summary)

        # Download summary
        st.download_button(label="⬇️ Download Summary", data=summary, file_name="summary.txt", mime="text/plain")
    else:
        st.error("Could not extract text from the PDF!")

