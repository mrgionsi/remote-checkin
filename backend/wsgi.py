"""
WSGI entry point for the Flask application.
"""
#pylint: disable=C0303,E0401

from main import app

if __name__ == '__main__':
    app.run()
