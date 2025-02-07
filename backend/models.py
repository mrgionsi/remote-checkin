from sqlalchemy import Column, Integer, BigInteger, String, Date, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from database import Base

class Room(Base):
    __tablename__ = "room"
    
    id = Column(BigInteger, Sequence("room_id_seq"), primary_key=True, index=True)
    name = Column(String)
    capacity = Column(Integer)
    id_structure = Column(BigInteger, ForeignKey("structure.id"))

    structure = relationship("Structure", back_populates="rooms")

    def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "capacity": self.capacity,
                "id_structure": self.id_structure,
            }
class AdminStructure(Base):
    __tablename__ = "admin_structure"

    id_user = Column(BigInteger, ForeignKey("user.id"), primary_key=True)
    id_structure = Column(BigInteger, ForeignKey("structure.id"), primary_key=True)


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, Sequence("role_id_seq"), primary_key=True)
    name = Column(String)  # Fixed


# Association Table for Many-to-Many between Client and Reservation
class ClientReservations(Base):
    __tablename__ = "client_reservations"

    id_reservation = Column(BigInteger, ForeignKey("reservation.id"), primary_key=True)
    id_client = Column(BigInteger, ForeignKey("client.id"), primary_key=True)


class Client(Base):
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

    reservations = relationship("Reservation", secondary="client_reservations", back_populates="clients")  # FIXED


class Reservation(Base):
    __tablename__ = "reservation"

    id = Column(BigInteger, Sequence("reservation_id_seq"), primary_key=True, index=True)
    id_reference = Column(String(500), nullable=False)  # "booking or airbnb"
    start_date = Column(Date)
    end_date = Column(Date)
    id_room = Column(BigInteger, ForeignKey("room.id"))

    room = relationship("Room")
    clients = relationship("Client", secondary="client_reservations", back_populates="reservations")  # FIXED


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, Sequence("user_id_seq"), primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    password = Column(String)
    username = Column(String)
    id_role = Column(Integer, ForeignKey("role.id"))

    role = relationship("Role")


class Structure(Base):
    __tablename__ = "structure"

    id = Column(BigInteger, Sequence("structure_id_seq"), primary_key=True, index=True)
    name = Column(String)  # Fixed
    street = Column(String)  # Fixed
    city = Column(String)  # Fixed

    rooms = relationship("Room", back_populates="structure")
