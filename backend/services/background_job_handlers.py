"""Background job handlers."""

from datetime import datetime, timezone

from models import Client, ClientReservations, Reservation, Room, User
from services.portale_alloggi_service import PortaleAlloggiService
from utils.encryption_utils import decrypt_password

PORTALE_ALLOGGI_SUBMIT_JOB = "portale_alloggi_submit"


class JobExecutionError(Exception):
    """Raised when a background job cannot be completed successfully."""


def _prepare_reservation_data(reservation):
    """Build payload expected by Portale Alloggi service."""
    duration = 3
    if reservation.start_date and reservation.end_date:
        duration = max(1, (reservation.end_date - reservation.start_date).days)

    return {
        "id": reservation.id,
        "id_reference": reservation.id_reference,
        "start_date": reservation.start_date,
        "end_date": reservation.end_date,
        "duration": duration,
        "name_reference": reservation.name_reference,
        "email": reservation.email,
        "telephone": reservation.telephone,
    }


def handle_portale_alloggi_submit(db_session, payload):
    """Process Portale Alloggi real submission job."""
    reservation_id = payload.get("reservation_id")
    user_id = payload.get("user_id")

    reservation = db_session.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise JobExecutionError("Reservation not found")

    room = db_session.query(Room).filter(Room.id == reservation.id_room).first()
    if not room:
        raise JobExecutionError("Room not found")

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise JobExecutionError("User not found")

    if not user.portale_username or not user.portale_password or not user.portale_wskey:
        raise JobExecutionError("Portale Alloggi credentials not configured")

    clients = (
        db_session.query(Client)
        .join(ClientReservations, Client.id == ClientReservations.id_client)
        .filter(ClientReservations.id_reservation == reservation.id)
        .all()
    )
    if not clients:
        raise JobExecutionError("No guests found")

    portale_service = PortaleAlloggiService(
        username=user.portale_username,
        password=decrypt_password(user.portale_password),
        ws_key=user.portale_wskey,
    )

    result = portale_service.submit_guest_registration(
        [client.to_dict() for client in clients],
        _prepare_reservation_data(reservation),
    )

    if not result.get("success", False):
        raise JobExecutionError(str(result.get("result") or "Portale Alloggi rejected payload"))

    reservation.portale_alloggi_sent = True
    reservation.portale_alloggi_sent_at = datetime.now(timezone.utc)
    reservation.portale_alloggi_response = str(result.get("result", ""))

    return {
        "reservation_id": reservation.id,
        "structure_id": room.id_structure,
        "result": result,
    }


def execute_job_by_type(db_session, *, job_type, payload):
    """Dispatch job execution by type and return serializable result."""
    if job_type == PORTALE_ALLOGGI_SUBMIT_JOB:
        return handle_portale_alloggi_submit(db_session, payload)
    raise JobExecutionError(f"Unsupported job_type: {job_type}")
