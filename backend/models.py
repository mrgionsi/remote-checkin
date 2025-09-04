"""
Models module for the remote check-in system.

This module defines the SQLAlchemy models used for the application's database,
including Room, Client, Reservation, and others.
"""

from datetime import date, datetime
from sqlalchemy import Column, Integer, BigInteger, String, Date, ForeignKey, Sequence, Boolean, DateTime
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
    document_type = Column(String)

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
            "document_type": self.document_type,
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
    status = Column(String, default='Pending') #Approved, Pending, Declined, Sent back to customer
    name_reference = Column(String, default='Not available')
    email = Column(String, nullable=False)
    telephone = Column(String, default='')


    room = relationship("Room", lazy="joined")
    clients = relationship(
        "Client", secondary="client_reservations", back_populates="reservations"
    )

    def to_dict(self):
        """
        Return a serializable dict representing this Reservation.
        
        The returned dictionary contains the reservation's identifiers, date range,
        status and contact info. If the related Room is loaded, its full serialized
        dictionary is included under the "room" key; otherwise "room" is None.
        
        Returns:
            dict: {
                "id": int,
                "id_reference": str,
                "start_date": datetime,
                "end_date": datetime,
                "room": dict | None,
                "status": str,
                "name_reference": str,
                "email": str,
                "telephone": str
            }
        """
        return {
            "id": self.id,
            "id_reference": self.id_reference,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "room": self.room.to_dict() if self.room else None,  # Include full room details
            "status": self.status,
            "name_reference": self.name_reference,
            'email': self.email,
            'telephone': self.telephone
        }

    def __repr__(self):
        """
        Return a concise, unambiguous string representation of the Reservation for debugging.
        
        The representation includes the reservation's primary key (`id`) and its `id_reference`.
        
        Returns:
            str: A developer-facing string like "<Reservation(id=..., id_reference=...)>".
        """
        return f"<Reservation(id={self.id}, id_reference={self.id_reference})>"


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): Unique identifier for the user.
        name (str): User's name.
        surname (str): User's surname.
        email (str): User's email address.
        telephone (str): User's telephone number.
    """
    __tablename__ = "user"

    id = Column(BigInteger, Sequence("user_id_seq"), primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String)
    telephone = Column(String)
    password = Column(String)
    username = Column(String)
    id_role = Column(Integer, ForeignKey("role.id"))

    role = relationship("Role")
    email_config = relationship("EmailConfig", back_populates="user", uselist=False)

    def to_dict(self):
        """
        Return a serializable dictionary of the User suitable for API responses.
        
        The dictionary includes the user's primary fields:
        - id, name, surname, email, telephone, username, id_role
        
        Returns:
            dict: Mapping of the above field names to their values.
        """
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "telephone": self.telephone,
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
        cin (str): CIN (Codice Identificativo Nazionale) of the structure.
    """
    __tablename__ = "structure"

    id = Column(BigInteger, Sequence("structure_id_seq"), primary_key=True, index=True)
    name = Column(String)
    street = Column(String)
    city = Column(String)
    cin = Column(String)

    rooms = relationship("Room", back_populates="structure")

    def to_dict(self):
        """
        Return a dictionary of the Structure's public fields.
        
        Includes the instance's id, name, street, city, and cin; suitable for JSON serialization.
        Returns:
            dict: Mapping with keys "id", "name", "street", "city", and "cin".
        """
        return {
            "id": self.id,
            "name": self.name,
            "street": self.street,
            "city": self.city,
            "cin": self.cin,
        }

    def __repr__(self):
        """
        Return a developer-friendly string representation of the Structure instance.
        
        The returned string includes the structure's id, name, and city and is intended for debugging/logging.
        Returns:
            str: Formatted representation like '<Structure(id=..., name=..., city=...)>'.
        """
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
        """
        Return a developer-facing string representation of the StructureReservationsView instance.
        
        Includes the view's key fields: structure_id, structure_name, reservation_id, id_reference,
        start_date, end_date, room_id, room_name, and status.
        """
        return (
            f"<StructureReservationsView(structure_id={self.structure_id}, "
            f"structure_name='{self.structure_name}', reservation_id={self.reservation_id}, "
            f"id_reference='{self.id_reference}', start_date={self.start_date}, "
            f"end_date={self.end_date}, room_id={self.room_id}, room_name='{self.room_name}', "
            f"status='{self.status}')>"
        )


class EmailConfig(Base):
    """
    Represents email configuration for a user.

    Attributes:
        id (int): Unique identifier for the email configuration.
        user_id (int): Foreign key referencing the user.
        mail_server (str): SMTP server address.
        mail_port (int): SMTP server port.
        mail_use_tls (bool): Whether to use TLS encryption.
        mail_use_ssl (bool): Whether to use SSL encryption.
        mail_username (str): Email username/address.
        mail_password (str): Encrypted email password.
        mail_default_sender_name (str): Default sender name.
        mail_default_sender_email (str): Default sender email.
        provider_type (str): Type of email provider (smtp, mailgun, sendgrid, etc.).
        provider_config (str): JSON string for provider-specific configuration.
        is_active (bool): Whether this configuration is active.
        created_at (datetime): When the configuration was created.
        updated_at (datetime): When the configuration was last updated.
    """
    __tablename__ = "email_config"

    id = Column(Integer, Sequence("email_config_id_seq"), primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    mail_server = Column(String, nullable=False)
    mail_port = Column(Integer, nullable=False)
    mail_use_tls = Column(Boolean, default=True)
    mail_use_ssl = Column(Boolean, default=False)
    mail_username = Column(String, nullable=False)
    mail_password = Column(String, nullable=False)  # Encrypted
    mail_default_sender_name = Column(String)
    mail_default_sender_email = Column(String, nullable=False)
    provider_type = Column(String, default='smtp')  # smtp, mailgun, sendgrid, etc.
    provider_config = Column(String)  # JSON string for provider-specific settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="email_config")

    def to_dict(self, include_password=False):
        """
        Return a dictionary representation of the EmailConfig instance.
        
        By default the returned `mail_password` is masked as `"***"`. Set `include_password=True`
        to include the actual password. `created_at` and `updated_at` are converted to ISO 8601
        strings or None if not set.
        
        Parameters:
            include_password (bool): If True, include the actual `mail_password`; otherwise mask it.
        
        Returns:
            dict: Serialized fields of the EmailConfig, including `id`, `user_id`, SMTP/provider
            settings, `is_active`, and `created_at`/`updated_at` as ISO 8601 strings or None.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mail_server": self.mail_server,
            "mail_port": self.mail_port,
            "mail_use_tls": self.mail_use_tls,
            "mail_use_ssl": self.mail_use_ssl,
            "mail_username": self.mail_username,
            "mail_password": self.mail_password if include_password else "***",  # Include password only if requested
            "mail_default_sender_name": self.mail_default_sender_name,
            "mail_default_sender_email": self.mail_default_sender_email,
            "provider_type": self.provider_type,
            "provider_config": self.provider_config,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """
        Return a concise developer-facing representation of the EmailConfig.
        
        The string includes the instance's id, user_id, and provider_type and is intended for debugging/logging.
        
        Returns:
            str: Representation in the form "<EmailConfig(id=<id>, user_id=<user_id>, provider_type=<provider_type>)>"
        """
        return f"<EmailConfig(id={self.id}, user_id={self.user_id}, provider_type={self.provider_type})>"
