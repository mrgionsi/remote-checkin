#pylint: disable=E0611,E0401,W0719,C0301,C0303
"""
db_utils.py

This module provides utility functions for interacting with the database, specifically for operations related to
clients, reservations, and their associations. It includes functions to retrieve, update, and link client and reservation data.

Functions:
    - get_reservation_by_id: Retrieves a reservation by its reference ID.
    - get_client_by_cf: Retrieves a client by their fiscal code (CF).
    - add_or_update_client: Adds a new client or updates an existing client's information.
    - link_client_to_reservation: Links a client to a reservation by their IDs.

Usage Example:
    >>> from backend.utils.db_utils import get_reservation_by_id
    >>> reservation = get_reservation_by_id('reservation_id')
    >>> print(reservation)

Note:
    - Ensure that the database session is correctly managed using `get_db()`.
    - The functions rely on the SQLAlchemy ORM for interacting with the database.
    - Make sure the `Client`, `Reservation`, and `ClientReservations` models are properly defined in the application.
"""

from datetime import datetime
from models import Client, ClientReservations, Reservation
from database import get_db
from app_logging.config import get_logger
from app_logging.utils import safe_extra_fields

# Configure logging
logger = get_logger(__name__)

def get_reservation_by_id(reservation_id):
    """
    Retrieves a reservation from the database by its reference ID.

    Parameters:
        reservation_id (str): The unique reference ID of the reservation.

    Returns:
        Reservation: The reservation object if found, or None if not.
    """
    with get_db() as db:
        return db.query(Reservation).filter(Reservation.id_reference == reservation_id).first()

def get_client_by_cf(cf):
    """
    Retrieves a client from the database by their fiscal code (CF).

    Parameters:
        cf (str): The fiscal code of the client.

    Returns:
        Client: The client object if found, or None if not.
    """
    with get_db() as db:
        return db.query(Client).filter(Client.cf == cf).first()

def _parse_date_field(value):
    """Parse a date field value."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {value}") from None


def _update_existing_client(db, client, form_data):
    """Update an existing client with form data."""
    client = db.merge(client)
    logger.info("Updating existing client", extra=safe_extra_fields({
        'client_id': client.id,
        'client_cf': client.cf,
        'operation': 'client_update'
    }))
    
    for key, value in form_data.items():
        if not hasattr(client, key) or key == 'reservationId':
            continue
            
        if key in ['birthday', 'data_emissione', 'data_scadenza']:
            value = _parse_date_field(value)
        
        setattr(client, key, value)
    
    db.commit()
    db.refresh(client)
    return client


def _create_new_client(db, form_data):
    """Create a new client from form data."""
    date_fields = ['birthday', 'data_emissione', 'data_scadenza']
    for date_field in date_fields:
        if date_field in form_data and form_data[date_field]:
            form_data[date_field] = _parse_date_field(form_data[date_field])
    
    form_data.pop('reservationId', None)
    logger.debug("Processing client form data", extra=safe_extra_fields({
        'form_fields': list(form_data.keys()) if form_data else [],
        'has_cf': 'cf' in form_data if form_data else False,
        'operation': 'form_data_processing'
    }))
    client = Client(**form_data)
    db.add(client)
    db.commit()
    return client


def add_or_update_client(form_data, client=None):
    """
    Adds a new client to the database or updates an existing client based on the provided form data.

    Parameters:
        form_data (dict): A dictionary containing client information (e.g., name, surname, birthday, etc.).
        client (Client, optional): An existing client object to update. If None, a new client is created.

    Returns:
        Client: The added or updated client object.

    Raises:
        Exception: If there is an error during the add or update process.
    """
    try:
        with get_db() as db:
            if client:
                client = _update_existing_client(db, client, form_data)
            else:
                client = _create_new_client(db, form_data)
            
            db.refresh(client)
            return client

    except Exception as e:
        db.rollback()
        logger.error("Error during client add or update", extra=safe_extra_fields({
            'client_cf': form_data.get('cf') if form_data else None,
            'error_type': type(e).__name__,
            'error_details': str(e),
            'operation_result': 'failed'
        }), exc_info=True)
        raise Exception(f"Error during client add or update: {str(e)}") from e




def link_client_to_reservation(reservation_id, client_id):
    """
    Links a client to a reservation by their IDs.

    Parameters:
        reservation_id (str): The ID of the reservation.
        client_id (str): The ID of the client.

    Returns:
        None: The function does not return anything but ensures the client is linked to the reservation.

    Raises:
        Exception: If there is an error during the linking process.
    """
    with get_db() as db:
        existing_link = db.query(ClientReservations).filter(
            ClientReservations.id_reservation == reservation_id,
            ClientReservations.id_client == client_id
        ).first()

        if not existing_link:
            client_reservation = ClientReservations(id_reservation=reservation_id, id_client=client_id)
            db.add(client_reservation)
            db.commit()
