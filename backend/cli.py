"""
Interactive terminal demo for the AI Skin & Hair Health Assistant.

Run:
    pip install -r requirements.txt
    python cli.py

Walks through: concern type -> symptoms -> optional photo -> type/budget/city
-> runs the LangGraph pipeline -> prints routine, products, reminders, and
(if flagged) offers to book a dermatologist appointment.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.build_graph import build_graph  # noqa: E402


def ask(prompt: str, default: str = "") -> str:
    val = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return val or default


def yn(prompt: str) -> bool:
    return ask(prompt + " (y/n)", "n").lower().startswith("y")


def print_section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print("=" * 60)
    print(" AI Skin & Hair Health Assistant -- Demo (LangGraph)")
    print("=" * 60)
    print("Disclaimer: this is a demo. It does not provide medical diagnosis.")

    app = build_graph()

    name = ask("Your name", "Guest")
    concern_type = ask("Is this about 'skin' or 'hair'?", "skin").lower()
    if concern_type not in ("skin", "hair"):
        concern_type = "skin"

    symptoms = ask("Describe what you're noticing (e.g. 'dry itchy patch on cheek')")
    image_path = ask("Path to a photo to analyze (optional, press Enter to skip)")
    if image_path and not os.path.exists(image_path):
        print(f"  (couldn't find '{image_path}', continuing without a photo)")
        image_path = ""

    type_prompt = "Skin type (oily/dry/combination/sensitive/normal/acne-prone)" \
        if concern_type == "skin" else \
        "Hair type (dry/oily/curly/damaged/colored/thinning/flaky-scalp/normal)"
    skin_or_hair_type = ask(type_prompt, "normal")
    budget = ask("Budget (low/medium/high)", "medium")
    city = ask("Your city (helps match a dermatologist if needed)", "")

    initial_state = {
        "user_name": name,
        "concern_type": concern_type,
        "symptoms_text": symptoms,
        "image_path": image_path or None,
        "skin_or_hair_type": skin_or_hair_type,
        "budget": budget,
        "city": city,
        "wants_booking": False,  # may flip below after we see the referral
    }

    # First pass: run everything up to (and including) the referral decision.
    result = app.invoke(initial_state)

    print_section("RISK ASSESSMENT")
    print(f"Risk level: {result['risk_level'].upper()}")
    for r in result["risk_reasons"]:
        print(f"  - {r}")

    print_section("YOUR ROUTINE")
    for k, v in result["routine"].items():
        label = k.replace("_", " ").title()
        if isinstance(v, list):
            print(f"{label}:")
            for item in v:
                print(f"  - {item}")
        else:
            print(f"{label}: {v}")

    print_section("RECOMMENDED PRODUCTS")
    for p in result["recommended_products"]:
        print(f"  - {p['name']}  (budget: {p['budget']})")

    print_section("HABIT REMINDERS")
    for r in result["reminders"]:
        print(f"  - {r}")

    print_section("DERMATOLOGIST GUIDANCE")
    print(result["referral_message"])

    if result["needs_dermatologist"]:
        if yn("\nWould you like to book a dermatologist appointment now?"):
            # Re-invoke with wants_booking=True; LangGraph will route
            # from 'referral' straight to the booking node this time.
            state_with_booking = dict(result)
            state_with_booking["wants_booking"] = True
            result = app.invoke(state_with_booking)

            appt = result.get("booking", {})
            print_section("APPOINTMENT CONFIRMED")
            if appt.get("status") == "confirmed":
                print(f"  Appointment ID : {appt['appointment_id']}")
                print(f"  Dermatologist  : {appt['dermatologist_name']} ({appt['specialty']})")
                print(f"  Date/Time      : {appt['datetime']}")
                print(f"  Reason         : {appt['reason']}")
            else:
                print(f"  Booking failed: {appt.get('reason', 'unknown error')}")

    print("\nThanks for using the demo!")


if __name__ == "__main__":
    main()
