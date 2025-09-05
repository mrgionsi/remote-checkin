# pylint: disable=C0301,E0611,E0401,W0718,E1101

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
    Validate a document image by running OCR and return extracted text or an error message.
    
    Attempts to load an image from image_path, convert it to grayscale, and extract text using pytesseract.
    Returns a tuple (bool, str): the boolean is True when OCR produced more than 10 non-whitespace characters; otherwise False.
    On failure the string contains a concise error message such as:
    - "Error: Could not load image. File may be corrupted or unsupported format." (image read failed)
    - "Error: Failed to process image. <exception message>" (cv2 conversion failure)
    - "OCR processing error: <error message>" (pytesseract failure)
    - "No valid text detected" (OCR ran but produced insufficient text)
    
    Parameters:
        image_path (str): Path to the image file to validate and OCR.
    
    Returns:
        tuple: (is_valid: bool, result: str) — is_valid indicates success; result is extracted text or an error message.
    """
    # Load the image
    image = cv2.imread(image_path)

    if image is None:
        return False, "Error: Could not load image. File may be corrupted or unsupported format."

    # Convert to grayscale for better OCR accuracy
    # Convert to grayscale for better OCR accuracy
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except Exception as e:  # More generic
        return False, f"Error: Failed to process image. {str(e)}"
    # Extract text using OCR
    try:
        text = pytesseract.image_to_string(gray)
    except pytesseract.TesseractError as e:
        return False, f"OCR processing error: {str(e)}"
    return (True, text) if len(text.strip()) > 10 else (False, "No valid text detected")
