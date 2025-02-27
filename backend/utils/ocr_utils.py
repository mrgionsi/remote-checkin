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
    text = pytesseract.image_to_string(gray)

    return (True, text) if len(text.strip()) > 10 else (False, "No valid text detected")
