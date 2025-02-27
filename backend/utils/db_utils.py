from datetime import datetime
from models import Client, ClientReservations, Reservation
from sqlalchemy.exc import SQLAlchemyError
from database import get_db

def get_reservation_by_id(reservation_id):
    with get_db() as db:
        return db.query(Reservation).filter(Reservation.id_reference == reservation_id).first()

def get_client_by_cf(cf):
    with get_db() as db:
        return db.query(Client).filter(Client.cf == cf).first()

def add_or_update_client(form_data, client=None):
    try:
        with get_db() as db:
            if client:
                # Ensure the client is part of the session
                client = db.merge(client)  # This will either return the existing object or attach it to the session

                print("Updating client:", client.id)

                # Update existing client
                for key, value in form_data.items():
                    if hasattr(client, key) and key != 'reservationId':
                        setattr(client, key, value if key != 'birthday' else datetime.strptime(value, "%Y-%m-%d"))

                db.commit()  # Commit the updates
                db.refresh(client)  # Refresh to get the latest values

            else:
                # Create new client
                form_data['birthday'] = datetime.strptime(form_data['birthday'], "%Y-%m-%d")
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
        raise Exception(f"Error during client add or update: {str(e)}")




def link_client_to_reservation(reservation_id, client_id):
    with get_db() as db:
        existing_link = db.query(ClientReservations).filter(
            ClientReservations.id_reservation == reservation_id,
            ClientReservations.id_client == client_id
        ).first()

        if not existing_link:
            client_reservation = ClientReservations(id_reservation=reservation_id, id_client=client_id)
            db.add(client_reservation)
            db.commit()
