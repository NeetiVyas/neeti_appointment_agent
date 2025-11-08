"""
A simple rule-based conversational agent that understands user messages and
returns a reply and updated context.

The `context` is a dict that carries conversation state across requests.
This is intentionally simple so you can later replace it with an LLM call.
"""

from rag.faq_rag import answer_faq
from tools.availability_tool import get_availability_for_date
from tools.booking_tool import create_booking
from agent.prompts import PROMPT_GREET, PROMPT_APPT_TYPE, PROMPT_PREFER_DATE

def handle_message(message: str, context: dict):
    """Return (reply, context)
    context fields used:
    - state: one of (start, asked_type, asked_date, suggested_slots, 
    collecting_info, ready_to_book, booked)
    - appointment_type
    - preferred_date
    - suggested_slots
    - patient (dict)
    """
    # Check if message is an FAQ question (rudimentary: contains keywords like 'insurance', 'hours')
    faq_keywords = ["insurance", "hours", "parking", "cancel", "covid"]
    if any(k in message.lower() for k in faq_keywords):
        ans = answer_faq(message)
        # keep context unchanged
        return ans, context
    state = context.get("state", "start")
    if state == "start":
        # greet and ask appointment type
        context["state"] = "asked_type"
        return PROMPT_APPT_TYPE, context
    
    if state == "asked_type":
        # assume user replied with type
        appt_type = message.strip().lower()
        context["appointment_type"] = appt_type
        context["state"] = "asked_date"
        return PROMPT_PREFER_DATE, context
    
    if state == "asked_date":
        # parse a date like '2024-01-15' or 'tomorrow' — for simplicity we expect ISO date
        preferred_date = message.strip()
        context["preferred_date"] = preferred_date
        # fetch slots using availability tool
        slots = get_availability_for_date(preferred_date,
        context.get("appointment_type", "consultation"))
        # pick first 4 slots and present them
        suggested = [s for s in slots if s["available"]][:5]
        if not suggested:
            context["state"] = "asked_date"
            return "No available slots on that date. Would you like me to look at other dates?", context
        context["suggested_slots"] = suggested
        context["state"] = "collecting_info"

        reply_lines = [f"I found these available slots on {preferred_date}:"]

        for s in suggested:
            reply_lines.append(f"- {s['start_time']} to {s['end_time']}")
            reply_lines.append("Which one works for you? Also please provide your full name, email and phone so I can confirm the booking.")
            return "\n".join(reply_lines), context
        
        if state == "collecting_info":
            # Expect the user to pick a start_time and give patient info in a simple freeform JSON-like string or structured message.
            # For beginners: we support a structured message like: "start_time:10:00; name:John Doe; email:john@example.com; phone:+1..."
            parts = [p.strip() for p in message.split(";")]
            data = {}
            for p in parts:
                if ":" in p:
                    k, v = p.split(":", 1)
                    data[k.strip()] = v.strip()
            if "start_time" not in data or "name" not in data or "email" not in data or "phone" not in data:
                return "Please provide start_time, name, email and phone in the format: start_time:10:00; name:John Doe; email:...; phone:...", context
            
            # build booking request
            req = {
                "appointment_type": context.get("appointment_type", "consultation"),
                "date": context.get("preferred_date"),
                "start_time": data["start_time"],
                "patient": {"name": data["name"], "email": data["email"], "phone":
                data["phone"]},
                "reason": data.get("reason", "")
            }
            booking = create_booking(req)
            if not booking:
                return "The selected slot is no longer available. Please choose another slot.", context
            context["state"] = "booked"
            context["booking"] = booking
            return f"All set! Your appointment is confirmed. Confirmation code: {booking['confirmation_code']}", context
        
        if state == "booked":
            return "You already have a booking. Do you want to reschedule or cancel?", context
        return "Sorry, I didn't understand that. Can you rephrase?", context