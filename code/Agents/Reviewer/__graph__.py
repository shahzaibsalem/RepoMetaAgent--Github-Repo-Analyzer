from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END

from Agents.Reviewer.__Review__ import make_reviewer_agent_node
from Agents.MetaDataAgent.nodes.GroqManager import GroqClientManager
from pathConfig import GROQ_MODEL


def build_reviewer_graph() -> StateGraph:
    """
    Builds a LangGraph for the Reviewer Agent.
    """

    groq_manager = GroqClientManager(model=GROQ_MODEL)

    workflow = StateGraph(dict)

    reviewer_node = make_reviewer_agent_node(groq_manager)

    workflow.add_node("reviewer_agent", reviewer_node)

    workflow.set_entry_point("reviewer_agent")
    workflow.set_finish_point("reviewer_agent")

    print("--- Reviewer graph compiled ---")

    return workflow.compile()
