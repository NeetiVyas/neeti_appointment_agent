from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..models.schemas import (
    AvailabilityResponse, Slot, BookRequest, BookResponse, AppointmentType
)
from ..tools.availability_tool import generate_slots
from ..tools.booking_tool import create_booking

router = APIRouter(prefix="/api/calendly", tags=["calendly"])

# Example in-repo data files (you can keep yours under data/)
# data/doctor_schedule.json structure suggestion:
# {
#   "2025-11-08": {
#       "working_hours": {"start": "09:00", "end": "17:00"},
#       "booked": [["10:00","10:30"], ["14:00","14:30"]]
#   },
#   ...
# }

import json, os

def _load_day(date: str):
    path = os.path.join("data", "doctor_schedule.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        all_days = json.load(f)
    return all_days.get(date)

@router.get("/availability", response_model=AvailabilityResponse)
def get_availability(date: str, appointment_type: AppointmentType):
    # Validate date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    day = _load_day(date) or {"working_hours": {"start": "09:00", "end": "17:00"}, "booked": []}
    slots = generate_slots(
        date=date,
        appointment_type=appointment_type,
        working_start=day["working_hours"]["start"],
        working_end=day["working_hours"]["end"],
        booked=[tuple(x) for x in day.get("booked", [])],
    )
    return AvailabilityResponse(date=date, available_slots=slots)

@router.post("/book", response_model=BookResponse)
def book(req: BookRequest):
    # Basic guard: ensure requested slot appears and is free
    avail = get_availability(date=req.date, appointment_type=req.appointment_type)
    found = next((s for s in avail.available_slots if s.start_time == req.start_time), None)
    if not found:
        raise HTTPException(status_code=409, detail="Requested start_time not available")
    if not found.available:
        raise HTTPException(status_code=409, detail="Requested slot is already booked")

    # Create booking (mock)
    return create_booking(req)
