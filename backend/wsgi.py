"""
WSGI entry point for the Flask application.
"""
#pylint: disable=E0401  # Import error for 'main' occurs during CI but works in runtime

from main import app

if __name__ == '__main__':
    app.run()
