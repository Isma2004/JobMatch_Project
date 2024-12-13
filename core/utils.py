import fitz  # PyMuPDF for PDF text extraction
from pdf2image import convert_from_path
from pytesseract import image_to_string
import openai

openai.api_key = 'sk-proj-hf4tdKgcrCCDdEwI6kQ70pwfzb9s3Vy6e9lv2tAtLJGOUEKfZ1nH8x69Uze37SP_S8s-NoiT3BlbkFJNAdXDwDpxdDc38guE2DCtvLhpp-yv1U9-nA4C6UoT6qurDN3FSWdGOHWJOckhiBeh43PmvIMMA'


def extract_text_from_pdf(pdf_stream):
    """
    Extracts text from a PDF file. Fallbacks to OCR if no text is extracted.
    """
    try:
        # Attempt to extract text using PyMuPDF
        with fitz.open(stream=pdf_stream.read(), filetype="pdf") as pdf_document:
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text += page.get_text()

        # Log extracted text
        print("Extracted Text Using PyMuPDF:", text)

        # If no text is extracted, fallback to OCR
        if not text.strip():
            print("No text extracted. Falling back to OCR.")
            pdf_stream.seek(0)  # Reset stream for OCR
            images = convert_from_path(pdf_stream.name)
            for image in images:
                ocr_text = image_to_string(image)
                print("OCR Extracted Text:", ocr_text)
                text += ocr_text

        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "Unable to parse resume. Please ensure it is in a readable format."


def parse_resume(resume_text):
    """
    Simulates resume parsing using OpenAI API.
    Expects resume_text as a string.
    """
    messages = [
        {
            "role": "user",
            "content": (
                f"You are a resume parsing assistant. Extract key information from the following resume:\n\n"
                f"{resume_text}Information to extract: Personal Details, Education, Work Experience, Skills, "
                "Personal Projects, Certificates if any. And make sure to be as detailed as possible"
            ),
        }
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
        )
        parsed_content = response.choices[0].message['content'].strip()
        return parsed_content
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return "Parsing failed. Ensure the file is readable and retry."