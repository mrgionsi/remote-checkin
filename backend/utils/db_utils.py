#pylint: disable=E0611,E0401,W0719,C0301
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
                # Ensure the client is part of the session
                client = db.merge(client)  # This will either return the existing object or attach it to the session

                print("Updating client:", client.id)

                # Update existing client
                for key, value in form_data.items():
                    if hasattr(client, key) and key != 'reservationId':
                        # Handle date fields
                        if key in ['birthday', 'data_emissione', 'data_scadenza']:
                            try:
                                if value:  # Only convert if value is not None/empty
                                    value = datetime.strptime(value, "%Y-%m-%d")
                                else:
                                    value = None
                            except ValueError:
                                raise ValueError(f"Invalid date format for {key}: {value}") from None
                        setattr(client, key, value)
                db.commit()  # Commit the updates
                db.refresh(client)  # Refresh to get the latest values

            else:
                # Create new client
                # Handle date fields for new client
                date_fields = ['birthday', 'data_emissione', 'data_scadenza']
                for date_field in date_fields:
                    if date_field in form_data and form_data[date_field]:
                        try:
                            form_data[date_field] = datetime.strptime(form_data[date_field], "%Y-%m-%d")
                        except ValueError as e:
                            raise ValueError(f"Invalid date format for {date_field}: {form_data.get(date_field)}") from e
                
                form_data.pop('reservationId', None)  # Remove if present
                print(form_data)
                client = Client(**form_data)
                db.add(client)  # Add new client to the session
                db.commit()  # Commit to save the new client

            # Ensure the object is properly persisted
            db.refresh(client)
            return client

    except Exception as e:
        # Rollback in case of error
        db.rollback()
        print(f"Error during client add or update: {str(e)}")
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
