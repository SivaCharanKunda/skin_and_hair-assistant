"""
Mock booking system.

Loads a small dermatologist directory from data/dermatologists.json and
"books" an appointment by writing a record to data/appointments.json.
In production this would call a real scheduling API (e.g. Calendly-style
provider, hospital EHR, etc.) -- the graph node using this only cares
about the return shape, so swapping the backend later is low-risk.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

_DIR_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dermatologists.json")
_APPT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "appointments.json")
_APPT_FALLBACK = os.path.join(tempfile.gettempdir(), "skin_hair_appointments.json")

with open(_DIR_PATH, "r", encoding="utf-8") as f:
    _DERMATOLOGISTS: List[Dict[str, Any]] = json.load(f)


def _appointments_path() -> str:
    """Prefer data/appointments.json; fall back to the system temp dir if
    the filesystem is read-only (e.g. on serverless platforms like Vercel)."""
    try:
        d = os.path.dirname(_APPT_PATH)
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".write_test")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
        return _APPT_PATH
    except OSError:
        return _APPT_FALLBACK


def _load_appointments() -> List[Dict[str, Any]]:
    path = _appointments_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_appointments(appts: List[Dict[str, Any]]) -> None:
    with open(_appointments_path(), "w", encoding="utf-8") as f:
        json.dump(appts, f, indent=2)


def find_dermatologist(city: Optional[str], concern_type: str) -> Dict[str, Any]:
    """Very simple matching: prefer same city, then specialty relevance."""
    def score(d):
        s = 0
        if city and d["city"].lower() == city.lower():
            s += 2
        if concern_type == "hair" and "trichology" in d["specialty"].lower():
            s += 1
        return -s  # lower (more negative) sorts first

    ranked = sorted(_DERMATOLOGISTS, key=score)
    return ranked[0] if ranked else {}


def book_appointment(
    user_name: str,
    city: Optional[str],
    concern_type: str,
    risk_reasons: List[str],
) -> Dict[str, Any]:
    derm = find_dermatologist(city, concern_type)
    if not derm or not derm.get("slots"):
        return {"status": "failed", "reason": "No dermatologist available right now."}

    slot = derm["slots"][0]  # take the earliest open slot (mock)
    appointment = {
        "appointment_id": str(uuid.uuid4())[:8],
        "patient_name": user_name or "Guest",
        "dermatologist_id": derm["id"],
        "dermatologist_name": derm["name"],
        "specialty": derm["specialty"],
        "datetime": slot,
        "reason": ", ".join(risk_reasons) if risk_reasons else "General consultation",
        "booked_at": datetime.now().isoformat(timespec="seconds"),
        "status": "confirmed",
    }

    appts = _load_appointments()
    appts.append(appointment)
    _save_appointments(appts)

    # remove the booked slot so a second booking demo doesn't double-book it
    derm["slots"].remove(slot)

    return appointment
