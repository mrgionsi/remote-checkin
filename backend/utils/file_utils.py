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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder, filename):
    """
    Save the uploaded file to the specified folder with the given filename.
    
    Parameters:
        file (FileStorage): The file to be saved.
        folder (str): The target folder where the file will be saved.
        filename (str): The name of the file to be saved.
    
    Returns:
        str: The path to the saved file.
    """
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    return filepath
