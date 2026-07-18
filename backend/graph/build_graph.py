"""
Wires all nodes into a single LangGraph StateGraph.

Flow:
    START
      -> intake                 (parse symptom text for red flags)
      -> image_analysis         (heuristic photo analysis, if a photo was given)
      -> risk_assessment        (combine both into a risk level)
      -> routine_recommendation
      -> product_recommendation
      -> reminders
      -> referral               (decide if a dermatologist is needed)
      -> [conditional] booking_node   -- only if high risk AND user wants to book
      -> END
"""

from langgraph.graph import StateGraph, START, END

from .state import AssistantState
from .nodes import (
    intake_node,
    image_analysis_node,
    risk_assessment_node,
    routine_recommendation_node,
    product_recommendation_node,
    reminder_node,
    referral_node,
    booking_node,
    route_after_referral,
)


def build_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("intake", intake_node)
    graph.add_node("image_analysis", image_analysis_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("routine_recommendation", routine_recommendation_node)
    graph.add_node("product_recommendation", product_recommendation_node)
    graph.add_node("reminders", reminder_node)
    graph.add_node("referral", referral_node)
    graph.add_node("booking", booking_node)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "image_analysis")
    graph.add_edge("image_analysis", "risk_assessment")
    graph.add_edge("risk_assessment", "routine_recommendation")
    graph.add_edge("routine_recommendation", "product_recommendation")
    graph.add_edge("product_recommendation", "reminders")
    graph.add_edge("reminders", "referral")

    graph.add_conditional_edges(
        "referral",
        route_after_referral,
        {"booking": "booking", "end": END},
    )
    graph.add_edge("booking", END)

    return graph.compile()
