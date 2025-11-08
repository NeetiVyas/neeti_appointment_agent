from datetime import datetime, time, timedelta
from typing import List
from ..models.schemas import Slot, APPT_DURATIONS

def _to_dt(date_str: str, hhmm: str):
    return datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")

def _to_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")

def generate_slots(
    date: str,
    appointment_type: str,
    working_start: str = "09:00",
    working_end: str = "17:00",
    booked: List[tuple[str, str]] | None = None,
) -> List[Slot]:
    """Return slot grid for the day with available flag, honoring durations."""
    dur = APPT_DURATIONS[appointment_type]
    start = _to_dt(date, working_start)
    end   = _to_dt(date, working_end)
    step  = timedelta(minutes=dur)
    booked = booked or []

    # normalize booked to datetime tuples
    booked_dt = [(_to_dt(date, s), _to_dt(date, e)) for s, e in booked]

    slots: List[Slot] = []
    cur = start
    while cur + step <= end:
        nxt = cur + step

        # conflict if any booked overlaps the interval [cur, nxt)
        available = True
        for b_s, b_e in booked_dt:
            if not (nxt <= b_s or cur >= b_e):
                available = False
                break

        slots.append(Slot(start_time=_to_hhmm(cur), end_time=_to_hhmm(nxt), available=available))
        cur = nxt

    return slots
