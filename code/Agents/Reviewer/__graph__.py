from typing import List, Union , Dict, Any, Callable, TypedDict
from langgraph.graph import StateGraph, END

from Agents.Reviewer.__Review__ import make_reviewer_agent_node
from Agents.MetaDataAgent.nodes.GroqManager import GroqClientManager
from pathConfig import GROQ_MODEL

class ReviewerState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    readme_md: str
    missing_docs: List[str]
    content_text: str
    
    spacy_keywords: List[str]
    gazetteer_keywords: List[str]
    llm_keywords: List[str]
    union_list: List[str]
    keywords: List[Dict[str, str]]
    
    suggested_title: str
    short_summary: str
    long_summary: str
    github_topics: List[str]
    
    final_output: Dict[str, Union[str, List, Dict]]

    review_report: str 

def build_reviewer_graph() -> StateGraph:
    """
    Builds a LangGraph for the Reviewer Agent.
    """

    groq_manager = GroqClientManager(model=GROQ_MODEL)

    workflow = StateGraph(ReviewerState)

    reviewer_node = make_reviewer_agent_node(groq_manager)

    workflow.add_node("reviewer_agent", reviewer_node)

    workflow.set_entry_point("reviewer_agent")
    workflow.set_finish_point("reviewer_agent")

    print("--- Reviewer graph compiled ---")

    return workflow.compile()
