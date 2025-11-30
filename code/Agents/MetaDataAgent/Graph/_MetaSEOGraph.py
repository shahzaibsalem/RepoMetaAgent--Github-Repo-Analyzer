from typing import Any, Dict, List, TypedDict, Union
from langgraph.graph import StateGraph, END

from Agents.MetaDataAgent.nodes.MetaDataGenerator import (
    generate_title_short_summary,
    generate_long_summary,
    generate_suggested_title,
    generate_topics_seo,
)
from Agents.MetaDataAgent.nodes.GroqManager import GroqClientManager    
from pathConfig import GROQ_MODEL 

# -----------------------------
# 1. Define State Dictionary
# -----------------------------
class MetaDataState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
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


# -----------------------------
# 2. Initialize Global Managers
# -----------------------------
GROQ_MANAGER = GroqClientManager(model=GROQ_MODEL)

# -----------------------------
# 3. Build the Sequential Graph
# -----------------------------
def build_meta_seo_graph():
    """
    Sequential Metadata SEO Graph:

    START -> Short Summary -> Long Summary -> Suggested Title -> Topics/SEO -> END
    """

    workflow = StateGraph(MetaDataState)

    # --- Instantiate Nodes ---
    short_summary_node = generate_title_short_summary(GROQ_MANAGER)
    long_summary_node = generate_long_summary(GROQ_MANAGER)
    suggested_title_node = generate_suggested_title(GROQ_MANAGER)
    topics_seo_node = generate_topics_seo(GROQ_MANAGER)

    # --- Register Nodes ---
    workflow.add_node("START", lambda state: {})  # entry node
    workflow.add_node("short_summary_node", short_summary_node)
    workflow.add_node("long_summary_node", long_summary_node)
    workflow.add_node("suggested_title_node", suggested_title_node)
    workflow.add_node("topics_seo_node", topics_seo_node)

    # --- Define Sequential Edges ---
    workflow.add_edge("START", "short_summary_node")
    workflow.add_edge("short_summary_node", "long_summary_node")
    workflow.add_edge("long_summary_node", "suggested_title_node")
    workflow.add_edge("suggested_title_node", "topics_seo_node")
    workflow.add_edge("topics_seo_node", END)

    workflow.set_entry_point("START")

    print("--- ✅ Sequential Metadata SEO Graph Built Successfully ---")
    return workflow.compile()
