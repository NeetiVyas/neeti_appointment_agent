import uuid, random, string
from ..models.schemas import BookRequest, BookResponse

def _code(n=6):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))

def create_booking(req: BookRequest) -> BookResponse:
    # In a real impl, persist to DB; here we return a mock confirmation.
    booking_id = f"APPT-{uuid.uuid4().hex[:8].upper()}"
    confirmation_code = _code()
    return BookResponse(
        booking_id=booking_id,
        confirmation_code=confirmation_code,
        details={
            "appointment_type": req.appointment_type,
            "date": req.date,
            "start_time": req.start_time,
            "patient": req.patient.model_dump(),
            "reason": req.reason,
        },
    )
