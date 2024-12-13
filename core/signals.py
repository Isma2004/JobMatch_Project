from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CandidateProfile
from .utils import parse_resume
import fitz  

@receiver(post_save, sender=CandidateProfile)
def parse_resume_on_creation(sender, instance, **kwargs):
    print("Signal triggered: Parsing resume...")
    if instance.resume and not instance.parsed_resume:
        print("Resume file exists and is not yet parsed...")
        try:
            with open(instance.resume.path, 'rb') as file:
                pdf_document = fitz.open(stream=file.read(), filetype="pdf")
                
                # Extract text from the PDF
                resume_text = ""
                for page_num in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_num)
                    resume_text += page.get_text()

                print(f"Extracted Text: {resume_text}")

                parsed_data = parse_resume(resume_text)
                
                # Check if parsed_data is not empty
                if parsed_data:
                    print("Resume parsed successfully.")
                    instance.parsed_resume = parsed_data  # Save parsed data to the candidate profile
                    instance.save()  # Save the updated instance
                else:
                    print("Parsing returned no data.")
        except Exception as e:
            print(f"Error while parsing the resume: {str(e)}")
