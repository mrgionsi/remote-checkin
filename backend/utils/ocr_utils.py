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
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError


MIN_TEXT_LENGTH = 10
MIN_OCR_CONFIDENCE = 45.0


def _preprocess_variants(image):
    """Generate OCR-friendly image variants."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=11)

    adaptive = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
    )
    otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return {
        "gray": gray,
        "adaptive": adaptive,
        "otsu": otsu,
    }


def _extract_with_confidence(image_variant):
    """Run OCR once and return extracted text and average confidence."""
    config = "--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        image_variant, config=config, output_type=pytesseract.Output.DICT
    )
    text = " ".join(
        str(token).strip()
        for token in data.get("text", [])
        if str(token).strip()
    )

    confidences = []
    for conf in data.get("conf", []):
        try:
            conf_val = float(conf)
        except (TypeError, ValueError):
            continue
        if conf_val >= 0:
            confidences.append(conf_val)

    average_confidence = float(np.mean(confidences)) if confidences else 0.0
    return text, average_confidence

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
        dict: Validation payload with:
            - valid (bool): True when OCR text and confidence pass validation.
            - error (str | None): Error message when invalid, empty when valid.
            - extracted_text (str): OCR text extracted from the best variant.
            - confidence (float | None): Average OCR confidence for the chosen variant.
            - variant (str | None): Image preprocessing variant used for the result.
    """
    # Load the image
    image = cv2.imread(image_path)

    if image is None:
        return {
            "valid": False,
            "error": "Error: Could not load image. File may be corrupted or unsupported format.",
            "extracted_text": "",
            "confidence": 0.0,
            "variant": None,
        }

    try:
        variants = _preprocess_variants(image)
    except Exception as e:  # pylint: disable=W0718
        return {
            "valid": False,
            "error": f"Error: Failed to process image. {str(e)}",
            "extracted_text": "",
            "confidence": 0.0,
            "variant": None,
        }

    best = {
        "valid": False,
        "error": "No valid text detected",
        "extracted_text": "",
        "confidence": 0.0,
        "variant": None,
    }

    try:
        for variant_name, variant_image in variants.items():
            text, confidence = _extract_with_confidence(variant_image)
            stripped_text = text.strip()
            is_valid = len(stripped_text) >= MIN_TEXT_LENGTH and confidence >= MIN_OCR_CONFIDENCE

            if confidence > best["confidence"] or (is_valid and not best["valid"]):
                best = {
                    "valid": is_valid,
                    "error": "" if is_valid else "No valid text detected",
                    "extracted_text": text,
                    "confidence": round(confidence, 2),
                    "variant": variant_name,
                }

            if is_valid:
                return best
    except TesseractNotFoundError:
        return {
            "valid": False,
            "error": "OCR engine not available. Please try again later.",
            "extracted_text": "",
            "confidence": 0.0,
            "variant": None,
        }
    except pytesseract.TesseractError as e:
        return {
            "valid": False,
            "error": f"OCR processing error: {str(e)}",
            "extracted_text": "",
            "confidence": 0.0,
            "variant": None,
        }

    return best
