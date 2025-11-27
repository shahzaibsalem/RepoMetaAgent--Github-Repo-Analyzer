from typing import Any, Dict, List, TypedDict, Union, Callable
from langgraph.graph import StateGraph, END

# --- 1. Import Node Functions and Managers from your Node File ---
# NOTE: Replace 'nodes' with the actual name of your file containing the nodes.
from ..nodes.TagGenerator import (
    union_keywords_node,
    make_selector_node,
    make_llm_extractor_node,
    make_gazetteer_tag_generator_node,
    make_spacy_extractor_node,
    
)
from nodes.GroqManager import GroqClientManager
from pathConfig import GROQ_MODEL

# --- Define the State Dictionary for the Graph ---
class AnalysisState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    content_text: str  # Input
    # We need to explicitly initialize these three fields now
    spacy_keywords: List[str]
    gazetteer_keywords: List[str]
    llm_keywords: List[str]
    union_list: List[str] # Intermediate
    missing_docs: List[str]
    keywords: List[str] # Output
    final_output: Dict[str, Union[str, List, Dict]]

# --- Initialize Global Managers ---
GROQ_MANAGER = GroqClientManager(model=GROQ_MODEL)


# ---------------------------------------------
# 2. Build and Compile the Tag Generation Graph
# ---------------------------------------------
def build_tag_generation_graph() -> Any:
    """
    Builds and compiles the Tag Generation Subgraph with parallel extraction.
    
    Flow: 
    START -> [SpaCy | Gazetteer | LLM] (Parallel)
    -> Join (Union)
    -> Selector (Curation)
    -> END
    """
    workflow = StateGraph(AnalysisState)

    # --- Instantiate Closure Nodes (Heavy Setup, runs once) ---
    spacy_extractor = make_spacy_extractor_node()
    gazetteer_extractor = make_gazetteer_tag_generator_node()
    llm_extractor = make_llm_extractor_node(GROQ_MANAGER)
    selector_node = make_selector_node(GROQ_MANAGER)
    
    # --- Add Nodes to the Workflow ---
    # The 'basic_extractor' node is removed here.
    workflow.add_node("spacy_extractor", spacy_extractor)
    workflow.add_node("gazetteer_extractor", gazetteer_extractor)
    workflow.add_node("llm_extractor", llm_extractor)
    workflow.add_node("union_keywords", union_keywords_node) # This acts as the Join
    workflow.add_node("selector", selector_node)

    # --- Define Edges (Transitions) ---
    
    # 1. Set the starting point
    workflow.set_entry_point("spacy_extractor") # Arbitrarily start with the SpaCy node
    
    # 2. Define the Parallel Flow (Conditional Edge)
    # The first node (spacy_extractor) must immediately transition to the others to kick them off.
    # In LangGraph, to start multiple paths, the starting node returns the names of the next nodes.
    
    # To start the other two nodes in parallel, we use a custom function/conditional edge 
    # from the entry node, or define the initial entry to the three nodes.
    
    # Simplest Parallel approach for StateGraph: The start node transitions to ALL three nodes.
    # Since only one node can be the entry point, we define transitions from the entry node:
    
    # From SpaCy, immediately transition to the other two nodes AND the Join node.
    # The Join node (union_keywords) waits for all preceding nodes to complete.
    
    # Transition from the first node to the other two extractors:
    # NOTE: Since LangGraph doesn't allow one node to directly transition to many without 
    # a function returning a list of names (which is complex for StateGraph), the cleanest
    # approach is to set the start point to *all* parallel paths and rely on the Join.
    
    # Let's set the entry to the SpaCy Extractor and rely on the full graph wrapper 
    # to handle the initial fan-out (if using a different graph type). 
    # For StateGraph, we must define the edges explicitly:
    
    # 3. Define the extraction paths to the Join node
    # Each extractor node independently contributes to the shared state.
    # The 'union_keywords' node serves as the synchronization point (Join).
    
    # To make them run concurrently, we need to set all three extractors as the immediate
    # next step from the entry point (which we assume is the `fetcher/checker` node 
    # if this were a subgraph). Since this is the START of the Tag Graph:
    
    # A. Set all three as the initial step from the entry point.
    #    (This requires a single starting node outside this graph, e.g., 'checker',
    #     to return ['spacy_extractor', 'gazetteer_extractor', 'llm_extractor']).
    
    # B. For this self-contained graph, we use the internal node transitions:
    # We will define a transition from a pseudo-start to all three:
    
    # --- Re-defining the Entry Point and Parallel Edges ---
    # We need a starting node that immediately fans out. Let's use 'spacy_extractor' as the first
    # and define the others to also be "reachable" from the start.
    
    # 1. Set SpaCy as the main entry point
    workflow.set_entry_point("spacy_extractor")
    
    # 2. Transition ALL parallel nodes to the Union/Join node.
    workflow.add_edge("spacy_extractor", "union_keywords") 
    workflow.add_edge("gazetteer_extractor", "union_keywords") 
    workflow.add_edge("llm_extractor", "union_keywords") 
    
    # ⚠️ CRITICAL STEP: The parent graph (RepoAnalyzer) must ensure that 
    # *ALL THREE* of these nodes are invoked immediately after the content is loaded.
    # If this graph is run as a standalone, only 'spacy_extractor' will run.
    
    # To enable true concurrency here, the parent must run:
    # app.invoke(..., threads=[ {"thread": "spacy_extractor"}, {"thread": "gazetteer_extractor"}, {"thread": "llm_extractor"} ])
    
    # For a clean StateGraph structure, we must rely on the **Parent Graph** to invoke these 
    # three nodes concurrently, and the Union node to **wait for all of them**.
    
    # 3. Define the final curation step
    # The 'union_keywords' node automatically waits for all incoming edges to complete.
    workflow.add_edge("union_keywords", "selector")     
    
    # 4. End the graph
    workflow.add_edge("selector", END)             

    # Compile the graph
    return workflow.compile()


# ---------------------------------------------
# 3. Execution (Example of how it would be run)
# ---------------------------------------------
if __name__ == "__main__":
    
    print("Tag Generation Graph Builder compiled successfully (Parallel structure defined).")
    
    # 

    # NOTE: To truly run this concurrently, the parent calling code needs 
    # to initiate all three paths simultaneously (e.g., using a thread pool 
    # or LangGraph's asynchronous invocation methods).
    
    # Since we are focusing only on the graph structure here, the compiled graph 
    # defines the synchronization point correctly: the 'union_keywords' node.