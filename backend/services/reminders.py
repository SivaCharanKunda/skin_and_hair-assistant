from typing import List


def generate_reminders(concern_type: str, risk_level: str) -> List[str]:
    reminders = []
    if concern_type == "skin":
        reminders += [
            "Apply sunscreen every morning, even indoors near windows.",
            "Change your pillowcase at least once a week.",
            "Avoid touching your face with unwashed hands.",
            "Patch-test any new product on your inner arm for 24 hours first.",
        ]
    else:  # hair
        reminders += [
            "Avoid tying wet hair tightly; let it air-dry first.",
            "Oil/massage your scalp gently 1-2 times a week.",
            "Use a wide-tooth comb on wet hair to reduce breakage.",
            "Limit heat styling to 2-3 times a week, always with a heat protectant.",
        ]

    if risk_level in ("moderate", "high"):
        reminders.append("Track any changes (size, colour, itching, pain) with weekly photos.")
    return reminders
