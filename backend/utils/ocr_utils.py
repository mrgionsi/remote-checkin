# pylint: disable=C0301,E0611,E0401,W0718,E1101

"""
OCR utility functions for document validation.

This module provides functions for validating documents by extracting text using Optical Character Recognition (OCR).
It uses the Tesseract OCR engine and OpenCV for image processing.

Functions:
    - validate_document(image_path: str) -> dict:
        Extracts text from an image and validates if the document contains sufficient text.
        Returns a dictionary with validity flag, extracted text, confidence and error details.

Dependencies:
    - OpenCV (cv2) for image manipulation.
    - Pytesseract for optical character recognition (OCR).

"""
import os

import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError


MIN_TEXT_LENGTH = 10
MIN_OCR_CONFIDENCE = 30.0
OCR_TIMEOUT_SECONDS = float(os.getenv("OCR_TIMEOUT_SECONDS", "8"))
MAX_OCR_IMAGE_SIDE = int(os.getenv("MAX_OCR_IMAGE_SIDE", "2200"))
MIN_OCR_IMAGE_SIDE = int(os.getenv("MIN_OCR_IMAGE_SIDE", "1200"))


def _preprocess_variants(image):
    """Generate OCR-friendly image variants."""
    height, width = image.shape[:2]
    largest_side = max(height, width)
    if largest_side > MAX_OCR_IMAGE_SIDE:
        scale = MAX_OCR_IMAGE_SIDE / float(largest_side)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        height, width = image.shape[:2]
        largest_side = max(height, width)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=9)
    # Upscale only small inputs to a target side to avoid huge OCR matrices.
    normalized_input = denoised
    if 0 < largest_side < MIN_OCR_IMAGE_SIDE:
        scale = MIN_OCR_IMAGE_SIDE / float(largest_side)
        normalized_input = cv2.resize(
            denoised, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
    normalized = cv2.convertScaleAbs(normalized_input, alpha=1.25, beta=8)

    adaptive = cv2.adaptiveThreshold(
        normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
    )
    otsu = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return {
        "gray": normalized,
        "adaptive": adaptive,
        "otsu": otsu,
    }


def _extract_with_confidence(image_variant):
    """Run OCR with multiple page segmentation modes and keep the best result."""
    best_text = ""
    best_confidence = 0.0
    for config in ("--oem 3 --psm 6", "--oem 3 --psm 11"):
        data = pytesseract.image_to_data(
            image_variant,
            config=config,
            output_type=pytesseract.Output.DICT,
            timeout=OCR_TIMEOUT_SECONDS,
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
        if average_confidence > best_confidence:
            best_confidence = average_confidence
            best_text = text

    return best_text, best_confidence

def validate_document(image_path):
    """
    Validate a document image by running OCR and return a structured validation payload.
    
    Attempts to load an image from image_path, convert it to grayscale, and extract text using pytesseract.
    On failure the payload contains a concise error message such as:
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
                break
    except (TesseractNotFoundError, pytesseract.TesseractError, RuntimeError) as exc:
        error_message = "OCR engine not available. Please try again later."
        if isinstance(exc, pytesseract.TesseractError):
            error_message = f"OCR processing error: {str(exc)}"
        elif isinstance(exc, RuntimeError):
            error_message = "OCR timeout. Please upload a clearer or smaller image."
        best = {
            "valid": False,
            "error": error_message,
            "extracted_text": "",
            "confidence": 0.0,
            "variant": None,
        }

    return best
