from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal, Optional

AppointmentType = Literal["consultation", "followup", "physical", "specialist"]

APPT_DURATIONS = {
    "consultation": 30,
    "followup": 15,
    "physical": 45,
    "specialist": 60,
}

class Slot(BaseModel):
    start_time: str   # "HH:MM" 24h local to clinic
    end_time: str
    available: bool = True

class AvailabilityResponse(BaseModel):
    date: str         # "YYYY-MM-DD"
    available_slots: List[Slot]

class Patient(BaseModel):
    name: str
    email: EmailStr
    phone: str

class BookRequest(BaseModel):
    appointment_type: AppointmentType
    date: str         # "YYYY-MM-DD"
    start_time: str   # "HH:MM"
    patient: Patient
    reason: Optional[str] = None

class BookResponse(BaseModel):
    booking_id: str
    status: Literal["confirmed", "failed"] = "confirmed"
    confirmation_code: str
    details: dict = Field(default_factory=dict)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
