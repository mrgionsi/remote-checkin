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
    Return True if the filename is a simple name (not a path) and has an allowed image extension.
    
    Performs two checks: rejects filenames that are not equal to os.path.basename(filename) (simple guard against basic directory traversal), and verifies the extension after the last dot (case-insensitive) is contained in ALLOWED_EXTENSIONS.
    
    Parameters:
        filename (str): The filename to validate.
    
    Returns:
        bool: True if the filename is a bare name and its extension is allowed; False otherwise.
    """
        # Check for directory traversal attempts
    if os.path.basename(filename) != filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder, filename):
    """
    Save an uploaded file into the given folder using a sanitized filename.
    
    Creates the target folder if it does not exist, uses os.path.basename(filename)
    to avoid directory traversal, writes the file using file.save(), and returns the
    full path to the saved file. On failure (filesystem error) returns None.
    Parameters:
        file: File-like object providing a .save(path) method (e.g., Werkzeug FileStorage).
        folder (str): Destination directory path; will be created if missing.
        filename (str): Desired filename (only the basename is used).
    Returns:
        str|None: Full path to the saved file on success, or None if saving failed.
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
    Build a sanitized filename from name, surname, fiscal code, and suffix.
    
    Each component is reduced to the set of allowed characters (letters, digits, space, hyphen, underscore), trimmed, and truncated to a maximum of 32 characters if longer. The extension is normalized to lowercase with any leading dot removed. The resulting filename has the form:
        "<name>-<surname>-<cf>-<suffix>.<extension>"
    
    Parameters that are not obvious:
        cf (str): Fiscal code or similar identifier to include in the filename.
        suffix (str): Descriptor appended to the filename (e.g., "selfie", "frontimage").
        extension (str): File extension (default "jpg"); leading dot is ignored.
    
    Returns:
        str: The assembled, sanitized filename.
    
    Raises:
        ValueError: If any component becomes empty after removing disallowed characters.
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
