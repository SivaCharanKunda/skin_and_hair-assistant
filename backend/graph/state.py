"""
Shared state object that flows through the LangGraph graph.

Every node reads from and writes to this single dict-like state.
LangGraph merges whatever a node returns into the overall state.
"""

from typing import TypedDict, List, Dict, Optional, Any


class AssistantState(TypedDict, total=False):
    # ---- raw input from the user ----
    user_name: str
    concern_type: str            # "skin" or "hair"
    symptoms_text: str           # free text description from chat
    image_path: Optional[str]    # path to an uploaded photo, if any
    skin_or_hair_type: str       # e.g. "oily", "dry", "curly", "colored" ...
    budget: str                  # "low", "medium", "high"
    city: str                    # used to match a nearby dermatologist

    # ---- derived / analysis results ----
    image_analysis: Dict[str, Any]     # heuristic findings from the photo
    nlu: Dict[str, Any]                # parsed intent/keywords from symptoms_text
    risk_level: str                    # "low" | "moderate" | "high"
    risk_reasons: List[str]

    routine: Dict[str, Any]
    recommended_products: List[Dict[str, Any]]
    reminders: List[str]

    needs_dermatologist: bool
    referral_message: str

    # ---- booking ----
    wants_booking: bool                # user confirmed they want to book
    booking: Optional[Dict[str, Any]]

    # ---- conversation log (for the CLI / UI to render) ----
    messages: List[Dict[str, str]]
