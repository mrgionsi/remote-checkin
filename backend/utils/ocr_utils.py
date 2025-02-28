"""
OCR utility functions for document validation.

This module provides functions for validating documents by extracting text using Optical Character Recognition (OCR).
It uses the Tesseract OCR engine and OpenCV for image processing.

Functions:
    - validate_document(image_path: str) -> tuple:
        Extracts text from an image and validates if the document contains sufficient text.
        Returns a tuple containing a boolean value indicating the validity of the document
        and a string with either the extracted text or an error message.

Dependencies:
    - OpenCV (cv2) for image manipulation.
    - Pytesseract for optical character recognition (OCR).

"""

import cv2
import pytesseract

def validate_document(image_path):
    """
    Validate the document by extracting text using OCR.
    
    Parameters:
        image_path (str): The file path of the uploaded document.
    
    Returns:
        tuple: (bool, str) where bool indicates validity and str contains extracted text.
    """
    # Load the image
    image = cv2.imread(image_path)

    if image is None:
        return False, "Error: Could not load image. File may be corrupted or unsupported format."

    # Convert to grayscale for better OCR accuracy
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Extract text using OCR
    try:
        text = pytesseract.image_to_string(gray)
    except pytesseract.TesseractError as e:
        return False, f"OCR processing error: {str(e)}"
    return (True, text) if len(text.strip()) > 10 else (False, "No valid text detected")
