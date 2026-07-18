"""
Node functions for the Skin & Hair Health Assistant graph.

Each function takes the current AssistantState and returns a dict of the
fields it wants to update -- this is the standard LangGraph node pattern.
Keeping each node a thin wrapper around a `services/` function means the
"AI logic" can be upgraded later (e.g. symptoms_text NLU -> real LLM call,
image heuristics -> real vision model) without touching the graph wiring.
"""

from typing import Dict, Any
from .state import AssistantState
from services.image_analysis import analyze_image
from services.product_catalog import recommend_products
from services.reminders import generate_reminders
from services import booking as booking_service

SKIN_RED_FLAGS = [
    "bleeding", "oozing", "pus", "won't heal", "wont heal", "not healing",
    "growing fast", "changed color", "changed shape", "irregular border",
    "asymmetric", "fever", "spreading rapidly", "severe pain",
]

HAIR_RED_FLAGS = [
    "bald patch", "bald patches", "clumps falling", "sudden hair loss",
    "scarring", "burning scalp", "severe itching", "patchy", "sores on scalp",
    "bleeding scalp",
]


def intake_node(state: AssistantState) -> Dict[str, Any]:
    """Very light NLU: just scans the free-text for red-flag keywords.
    (Swap this for a real LLM-based intent parser in production.)"""
    text = (state.get("symptoms_text") or "").lower()
    concern_type = state.get("concern_type", "skin")
    flags = SKIN_RED_FLAGS if concern_type == "skin" else HAIR_RED_FLAGS
    matched = [kw for kw in flags if kw in text]

    return {
        "nlu": {
            "matched_red_flags": matched,
            "raw_text": text,
        }
    }


def image_analysis_node(state: AssistantState) -> Dict[str, Any]:
    image_path = state.get("image_path")
    if not image_path:
        return {"image_analysis": {}}
    result = analyze_image(image_path, state.get("concern_type", "skin"))
    return {"image_analysis": result}


def risk_assessment_node(state: AssistantState) -> Dict[str, Any]:
    reasons = []
    risk_level = "low"

    text_flags = state.get("nlu", {}).get("matched_red_flags", [])
    if text_flags:
        risk_level = "high"
        reasons.append(f"Symptom description mentions: {', '.join(text_flags)}")

    img = state.get("image_analysis") or {}
    if img.get("dark_spot_flag"):
        risk_level = "high"
        reasons.append("Photo shows an unusually dark, high-contrast patch")
    if img.get("redness_score", 0) > 0.75:
        risk_level = "moderate" if risk_level == "low" else risk_level
        reasons.append("Photo shows strong redness/inflammation")
    if img.get("texture_variance", 0) > 0.7:
        risk_level = "moderate" if risk_level == "low" else risk_level
        reasons.append("Photo shows notably uneven texture")

    if not reasons:
        reasons.append("No red-flag signs detected in the info provided")

    return {"risk_level": risk_level, "risk_reasons": reasons}


def routine_recommendation_node(state: AssistantState) -> Dict[str, Any]:
    concern_type = state.get("concern_type", "skin")
    t = state.get("skin_or_hair_type", "normal")

    if concern_type == "skin":
        routine = {
            "morning": ["Gentle cleanser", "Lightweight moisturizer", "Sunscreen SPF 30+"],
            "night": ["Cleanser", "Treatment serum (if suited to your type)", "Moisturizer"],
            "weekly": ["Gentle exfoliation 1-2x", "Hydrating mask if dry/sensitive"],
            "notes": f"Tailored for '{t}' skin type.",
        }
    else:
        routine = {
            "wash_days": ["Sulfate-free shampoo", "Conditioner focused on lengths, not scalp"],
            "between_washes": ["Scalp massage", "Avoid tight hairstyles"],
            "weekly": ["Deep conditioning mask 1x", "Oil treatment before wash day"],
            "notes": f"Tailored for '{t}' hair type.",
        }

    if state.get("risk_level") == "high":
        routine["caution"] = "Pause new actives/treatments until a dermatologist has checked this."

    return {"routine": routine}


def product_recommendation_node(state: AssistantState) -> Dict[str, Any]:
    products = recommend_products(
        concern_type=state.get("concern_type", "skin"),
        skin_or_hair_type=state.get("skin_or_hair_type", "normal"),
        budget=state.get("budget", "medium"),
    )
    return {"recommended_products": products}


def reminder_node(state: AssistantState) -> Dict[str, Any]:
    reminders = generate_reminders(
        state.get("concern_type", "skin"), state.get("risk_level", "low")
    )
    return {"reminders": reminders}


def referral_node(state: AssistantState) -> Dict[str, Any]:
    needs_derm = state.get("risk_level") == "high"
    if needs_derm:
        msg = (
            "Based on what you've shared, this looks like something a licensed "
            "dermatologist should examine in person rather than something to "
            "self-treat. I'd strongly recommend booking a consultation."
        )
    else:
        msg = (
            "Nothing here raises a red flag, but if things change or don't "
            "improve in a couple of weeks, it's still worth getting a "
            "professional opinion."
        )
    return {"needs_dermatologist": needs_derm, "referral_message": msg}


def booking_node(state: AssistantState) -> Dict[str, Any]:
    appt = booking_service.book_appointment(
        user_name=state.get("user_name", "Guest"),
        city=state.get("city"),
        concern_type=state.get("concern_type", "skin"),
        risk_reasons=state.get("risk_reasons", []),
    )
    return {"booking": appt}


def route_after_referral(state: AssistantState) -> str:
    """Conditional edge: only go to booking if flagged high-risk AND the
    user has said they want to book."""
    if state.get("needs_dermatologist") and state.get("wants_booking"):
        return "booking"
    return "end"
