from pdf2image import convert_from_path, convert_from_bytes
import requests
import os
import tempfile
import streamlit as st

def pdf_to_text_with_ocr(pdf_path, api_key, output_folder="output", dpi=200, delete_after_use=False):
    """
    Converts a PDF to images, checks file size, performs OCR, and deletes unused images.
    
    Parameters:
    - pdf_path (str): Path to the PDF file.
    - api_key (str): API key for OCR.Space.
    - output_folder (str): Folder for temporary images.
    - dpi (int): Resolution of images (default: 150).
    - delete_after_use (bool): Whether to delete images after OCR.
    
    Returns:
    - Extracted text from the PDF or exits if file size is too large.
    """
    os.makedirs(output_folder, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)
    extracted_text = ""
    image_paths = []

    for i, img in enumerate(images):
        image_path = os.path.join(output_folder, f"page_{i+1}.jpg")
        img.save(image_path, "JPEG", quality=95)  # Save with high quality
        image_paths.append(image_path)

        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > 1024 * 1024:  # 1MB
            print(f"Image {image_path} is too large ({file_size / 1024:.2f} KB). Please reduce size manually using dpi parameter.")
            return  # Exit the function

        # Perform OCR
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"image": image_file},
                data={"apikey": api_key, "OCREngine": 2, "isTable": True},
            )

        result = response.json()
        print(f"API Response recived for page {i}")  # Debugging step

        if "ParsedResults" in result:
            extracted_text += result["ParsedResults"][0]["ParsedText"] + "\n"
        else:
            print(f"Error: 'ParsedResults' missing. Full response: psge mo:{i}")
            extracted_text += f"\n[Error: OCR failed for this page {i}]\n"

    # Delete images if enabled
    if delete_after_use:
        for img_path in image_paths:
            os.remove(img_path)
        print("Temporary images deleted.")

    return extracted_text

def pdf_obj_to_text_with_ocr(pdf_file, api_key, dpi=100, delete_after_use=False):
    """
    Converts an uploaded PDF file from Streamlit into images, performs OCR, and optionally deletes images.

    Parameters:
    - pdf_file (BytesIO): Streamlit uploaded file.
    - api_key (str): API key for OCR.Space.
    - dpi (int): Resolution of images (default: 100).
    - delete_after_use (bool): Whether to delete temporary images after OCR.

    Returns:
    - str: Extracted text from the PDF.
    """
    pdf_file.seek(0)
    images = convert_from_bytes(pdf_file.read(), dpi=dpi)
    extracted_text = ""
    temp_files = []

    for i, img in enumerate(images):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image:
            img.save(temp_image.name, "JPEG", quality=95)
            temp_files.append(temp_image.name)
            if not os.path.exists(temp_image.name):
                st.write(f"Page {i+1}: Failed to create image")
                extracted_text += f"\n[Error: Image creation failed for page {i+1}]\n"
                continue

        with open(temp_image.name, 'rb') as image_file:
            try:
                response = requests.post(
                    "https://api.ocr.space/parse/image",
                    files={"image": image_file},
                    data={"apikey": api_key, "OCREngine": 2, "isTable": True},
                )
                response.raise_for_status()
                result = response.json()
                if "ParsedResults" in result and result["ParsedResults"]:
                    extracted_text += f"Page {i+1}: " + result["ParsedResults"][0]["ParsedText"] + "\n"
                else:
                    extracted_text += f"\n[Error: OCR failed for page {i+1} - No parsed results]\n"
            except requests.exceptions.RequestException as e:
                st.write(f"OCR API request failed for page {i+1}: {str(e)}")
                extracted_text += f"\n[Error: OCR API request failed for page {i+1} - {str(e)}]\n"

    if delete_after_use:
        for temp_file in temp_files:
            os.remove(temp_file)

    return extracted_text

# Example usage
if __name__ == "__main__":
    pdf_file = r"" 
