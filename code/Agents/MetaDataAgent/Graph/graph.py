from typing import Any, Dict, List, TypedDict, Union
from langgraph.graph import StateGraph, END

from Agents.MetaDataAgent.nodes.TagGenerator import (
    union_keywords_node,
    make_selector_node,
    make_llm_extractor_node,
    make_gazetteer_tag_generator_node,
    make_spacy_extractor_node,
)
from Agents.MetaDataAgent.nodes.GroqManager import GroqClientManager
from pathConfig import GROQ_MODEL


# -----------------------------
# 1. Define State Dictionary
# -----------------------------
class AnalysisState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    content_text: str
    spacy_keywords: List[str]
    gazetteer_keywords: List[str]
    llm_keywords: List[str]
    union_list: List[str]
    missing_docs: List[str]
    keywords: List[str]
    final_output: Dict[str, Union[str, List, Dict]]


# -----------------------------
# 2. Initialize Global Managers
# -----------------------------
GROQ_MANAGER = GroqClientManager(model=GROQ_MODEL)


# -----------------------------
# 3. Build and Compile Graph
# -----------------------------
def build_tag_generation_graph() -> Any:
    """
    Tag Generation Graph:
    
    START -> [SpaCy | Gazetteer | LLM] (Parallel)
            -> UNION (union_keywords_node)
            -> SELECTOR (make_selector_node)
            -> END
    """
    workflow = StateGraph(AnalysisState)

    # --- Instantiate nodes ---
    spacy_extractor = make_spacy_extractor_node()
    gazetteer_extractor = make_gazetteer_tag_generator_node()
    llm_extractor = make_llm_extractor_node(GROQ_MANAGER)
    selector_node = make_selector_node(GROQ_MANAGER)

    # --- Add nodes ---
    workflow.add_node("spacy_extractor", spacy_extractor)
    workflow.add_node("gazetteer_extractor", gazetteer_extractor)
    workflow.add_node("llm_extractor", llm_extractor)
    workflow.add_node("union_keywords", union_keywords_node)
    workflow.add_node("selector", selector_node)

    # --- Define Entry Point ---
    # Create a pseudo-start node that fans out to all extractors
    def start_node(state):
        return ["spacy_extractor", "gazetteer_extractor", "llm_extractor"]

    workflow.add_node("START", start_node)
    workflow.set_entry_point("START")

    # --- Connect Extractors to UNION node ---
    workflow.add_edge("spacy_extractor", "union_keywords")
    workflow.add_edge("gazetteer_extractor", "union_keywords")
    workflow.add_edge("llm_extractor", "union_keywords")

    # --- Connect UNION to SELECTOR, then END ---
    workflow.add_edge("union_keywords", "selector")
    workflow.add_edge("selector", END)

    return workflow.compile()


# -----------------------------
# 4. Example Execution
# -----------------------------
if __name__ == "__main__":
    print("Tag Generation Graph compiled successfully with parallel structure.")
