"""
Models module for the remote check-in system.

This module defines the SQLAlchemy models used for the application's database, 
including Room, Client, Reservation, and others.
"""

from datetime import date
from sqlalchemy import Column, Integer, BigInteger, String, Date, ForeignKey, Sequence
from sqlalchemy.orm import relationship
#pylint: disable=C0303
#pylint: disable=E0611
from database import Base


class Room(Base):
    """
    Represents a room in the system.

    Attributes:
        id (int): Unique identifier for the room.
        name (str): Name of the room.
        capacity (int): The maximum capacity of the room.
        id_structure (int): Foreign key referencing the associated structure.
    """
    __tablename__ = "room"

    id = Column(BigInteger, Sequence("room_id_seq"), primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    id_structure = Column(BigInteger, ForeignKey("structure.id"), nullable=False)

    structure = relationship("Structure", back_populates="rooms")

    def to_dict(self):
        """Return a dictionary representation of the Room instance."""
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "id_structure": self.id_structure,
        }

    def __repr__(self):
        return f"<Room(id={self.id}, name={self.name}, capacity={self.capacity})>"


class AdminStructure(Base):
    """
    Represents the association between users and structures.

    Attributes:
        id_user (int): Foreign key referencing the user.
        id_structure (int): Foreign key referencing the structure.
    """
    __tablename__ = "admin_structure"

    id_user = Column(BigInteger, ForeignKey("user.id"), primary_key=True)
    id_structure = Column(BigInteger, ForeignKey("structure.id"), primary_key=True)

    def to_dict(self):
        """Return a dictionary representation of the AdminStructure instance."""
        return {
            "id_user": self.id_user,
            "id_structure": self.id_structure,
        }

    def __repr__(self):
        return f"<AdminStructure(id_user={self.id_user}, id_structure={self.id_structure})>"


class Role(Base):
    """
    Represents a role in the system.

    Attributes:
        id (int): Unique identifier for the role.
        name (str): Name of the role.
    """
    __tablename__ = "role"

    id = Column(Integer, Sequence("role_id_seq"), primary_key=True)
    name = Column(String)

    def to_dict(self):
        """Return a dictionary representation of the Role instance."""
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class ClientReservations(Base):
# pylint: disable=R0903

    """
    Association table for many-to-many relationship between Client and Reservation.
    """
    __tablename__ = "client_reservations"

    id_reservation = Column(BigInteger, ForeignKey("reservation.id"), primary_key=True)
    id_client = Column(BigInteger, ForeignKey("client.id"), primary_key=True)

    def to_dict(self):
        """Return a dictionary representation of the ClientReservations instance."""
        return {
            "id_reservation": self.id_reservation,
            "id_client": self.id_client,
        }


class Client(Base):
    """
    Represents a client in the system.

    Attributes:
        id (int): Unique identifier for the client.
        name (str): Client's name.
        surname (str): Client's surname.
    """
    __tablename__ = "client"

    id = Column(BigInteger, Sequence("client_id_seq"), primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    birthday = Column(Date)
    street = Column(String)
    number_city = Column(String)
    city = Column(String)
    province = Column(String)
    cap = Column(String)
    telephone = Column(String)
    document_number = Column(String)
    cf = Column(String)

    reservations = relationship(
        "Reservation", secondary="client_reservations", back_populates="clients"
    )

    def to_dict(self):
        """Return a dictionary representation of the Client instance."""
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "birthday": self.birthday,
            "street": self.street,
            "number_city": self.number_city,
            "city": self.city,
            "province": self.province,
            "cap": self.cap,
            "telephone": self.telephone,
            "document_number": self.document_number,
            "cf": self.cf,
        }

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, surname={self.surname})>"


class Reservation(Base):
    """
    Represents a reservation in the system.

    Attributes:
        id (int): Unique identifier for the reservation.
        id_reference (str): Reference ID for the reservation.
        start_date (Date): Start date of the reservation.
        end_date (Date): End date of the reservation.
        id_room (int): Foreign key referencing the reserved room.
    """
    __tablename__ = "reservation"

    id = Column(BigInteger, Sequence("reservation_id_seq"), primary_key=True, index=True)
    id_reference = Column(String(500), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    id_room = Column(BigInteger, ForeignKey("room.id"))
    status = Column(String, default='Pending')
    name_reference = Column(String, default='Not available')


    room = relationship("Room")
    clients = relationship(
        "Client", secondary="client_reservations", back_populates="reservations"
    )

    def to_dict(self):
        """Return a dictionary representation of the Reservation instance."""
        return {
            "id": self.id,
            "id_reference": self.id_reference,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "id_room": self.id_room,
            "status": self.status,
            "name_reference": self.name_reference
        }

    def __repr__(self):
        return f"<Reservation(id={self.id}, id_reference={self.id_reference})>"


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): Unique identifier for the user.
        name (str): User's name.
        surname (str): User's surname.
    """
    __tablename__ = "user"

    id = Column(BigInteger, Sequence("user_id_seq"), primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    password = Column(String)
    username = Column(String)
    id_role = Column(Integer, ForeignKey("role.id"))

    role = relationship("Role")

    def to_dict(self):
        """Return a dictionary representation of the User instance."""
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "username": self.username,
            "id_role": self.id_role,
        }

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Structure(Base):
    """
    Represents a structure (building or organization) in the system.

    Attributes:
        id (int): Unique identifier for the structure.
        name (str): Name of the structure.
        street (str): Street address of the structure.
        city (str): City of the structure.
    """
    __tablename__ = "structure"

    id = Column(BigInteger, Sequence("structure_id_seq"), primary_key=True, index=True)
    name = Column(String)
    street = Column(String)
    city = Column(String)

    rooms = relationship("Room", back_populates="structure")

    def to_dict(self):
        """Return a dictionary representation of the Structure instance."""
        return {
            "id": self.id,
            "name": self.name,
            "street": self.street,
            "city": self.city,
        }

    def __repr__(self):
        return f"<Structure(id={self.id}, name={self.name}, city={self.city})>"

class StructureReservationsView(Base):
    """
    Represents the PostgreSQL view for structure-room-reservation.
    This is a read-only model.
    """
    __tablename__ = "structure_reservations"

    structure_id = Column(BigInteger)
    structure_name = Column(String)
    reservation_id = Column(BigInteger, primary_key=True)
    id_reference = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    room_id = Column(BigInteger)
    room_name = Column(String)
    status = Column(String)
    name_reference = Column(String)

    def to_dict(self)-> dict[str, str | int | date]:
        """Return a dictionary representation of the StructureReservationsView instance."""
        return {
            "structure_id": self.structure_id,
            "structure_name": self.structure_name,
            "reservation_id": self.reservation_id,
            "id_reference": self.id_reference,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "status": self.status,
        }

    def __repr__(self):
        return (
            f"<StructureReservationsView(structure_id={self.structure_id}, "
            f"structure_name='{self.structure_name}', reservation_id={self.reservation_id}, "
            f"id_reference='{self.id_reference}', start_date={self.start_date}, "
            f"end_date={self.end_date}, room_id={self.room_id}, room_name='{self.room_name}', "
            f"status='{self.status}')>"
        )
