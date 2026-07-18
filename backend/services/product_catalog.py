import json
import os
from typing import List, Dict, Any

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")

with open(_DATA_PATH, "r", encoding="utf-8") as f:
    _PRODUCTS: List[Dict[str, Any]] = json.load(f)


def recommend_products(
    concern_type: str,
    skin_or_hair_type: str,
    budget: str = "medium",
    max_results: int = 4,
) -> List[Dict[str, Any]]:
    """
    Simple rule-based filter + ranking over the mock catalog.
    Real version could swap this for a recommender model / vendor API,
    the graph node calling this doesn't need to change.
    """
    budget_rank = {"low": 0, "medium": 1, "high": 2}
    user_budget_rank = budget_rank.get(budget, 1)

    candidates = [
        p for p in _PRODUCTS
        if p["category"] == concern_type
        and (skin_or_hair_type in p["for_types"] or "all" in p["for_types"])
    ]

    if not candidates:
        # fall back to category-only match so we always suggest *something*
        candidates = [p for p in _PRODUCTS if p["category"] == concern_type]

    # prefer products at or below the user's budget rank, then by name for stability
    def sort_key(p):
        p_rank = budget_rank.get(p["budget"], 1)
        return (abs(p_rank - user_budget_rank), p["name"])

    candidates.sort(key=sort_key)
    return candidates[:max_results]
