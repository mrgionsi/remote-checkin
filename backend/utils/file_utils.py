#pylint: disable=E0611,E0401,W0719,C0301
"""
file_utils.py

This module provides utility functions for working with files. It includes operations like reading, writing,
file validation, and other file manipulation tasks required in the application.

Functions:
    - function_name_1: Description of function.
    - function_name_2: Description of function.
    - ...
    
Usage Example:
    >>> from backend.utils.file_utils import function_name_1
    >>> result = function_name_1('file_path')
    >>> print(result)

Note: Ensure that the required file permissions and paths are correctly set for all operations.
"""
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'uploads/'

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Parameters:
        filename (str): The name of the uploaded file.
    
    Returns:
        bool: True if file extension is allowed, False otherwise.
    """
        # Check for directory traversal attempts
    if os.path.basename(filename) != filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder, filename):
    """
    Save the uploaded file to the specified folder with the given filename.
    
    Parameters:
        file (FileStorage): The file to be saved.
        folder (str): The target folder where the file will be saved.
        filename (str): The name of the file to be saved.
    
    Returns:
        str: The path to the saved file on success, None on failure.
    
    Raises:
        OSError: If the folder doesn't exist or cannot be created.
        IOError: If the file cannot be saved.
    """
    try:
        # Ensure target folder exists
        os.makedirs(folder, exist_ok=True)
        # Sanitize filename (additional security)
        safe_filename = os.path.basename(filename)

        filepath = os.path.join(folder, safe_filename)
        file.save(filepath)
        return filepath
    except (OSError, IOError) as e:
        print(f"Error saving file: {e}")
        return None

def sanitize_filename(name, surname, cf, suffix, extension="jpg"):
    """
    Sanitize the input for filename creation, allowing only certain characters and limiting length.
    
    Parameters:
        name (str): The name part of the filename.
        surname (str): The surname part of the filename.
        cf (str): The cf part of the filename (fiscal code or similar).
        suffix (str): The suffix to be added at the end of the filename (e.g., 'selfie', 'frontimage').
        extension (str): The file extension (default 'jpg').
    
    Returns:
        str: A sanitized filename.
    
    Raises:
        ValueError: If any sanitized component is empty or exceeds length limits.
    """
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
    max_len = 32

    def sanitize_component(component):
        sanitized = "".join(c for c in component if c in allowed).strip()
        if not sanitized:
            raise ValueError("Filename component cannot be empty after sanitization.")
        if len(sanitized) > max_len:
            sanitized = sanitized[:max_len]
        return sanitized

    sanitized_name = sanitize_component(name)
    sanitized_surname = sanitize_component(surname)
    sanitized_cf = sanitize_component(cf)
    sanitized_suffix = sanitize_component(suffix)
    sanitized_extension = extension.lower().strip('.')

    filename = f"{sanitized_name}-{sanitized_surname}-{sanitized_cf}-{sanitized_suffix}.{sanitized_extension}"
    return filename
