# main.py

import os
import json
from typing import Dict, Any, List, TypedDict, Union
from langgraph.graph import StateGraph, END
# from langgraph.graph import CompiledGraph # Import for type hinting

# --- 1. Import the Graph Builders from their respective locations ---
# NOTE: Adjust these relative imports based on your exact file structure.
from Agents.RepoAnalyzerAgent.RepoAnalyzer import build_analyzer_graph
from Agents.MetaDataAgent.Graph._Tagsgraph import build_tag_generation_graph
from Agents.MetaDataAgent.Graph._MetaSEOGraph import build_meta_seo_graph
from Agents.Reviewer.__graph__ import build_reviewer_graph

# --- 2. Define the Complete, Unified State ---
# The state must include ALL fields used by BOTH graphs.
class UnifiedAnalysisState(TypedDict):
    # --- FIELDS FROM RepoAnalyzerAgent ---
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    missing_docs: List[str]
    #---------------------------------------

    # --- Metadata Fields ---
    suggested_title: str         
    short_summary: str           
    long_summary: str            
    github_topics: List[str]     
    # ---------------------------

    # Keyword fields (used by Tag Generation Graph)
    content_text: str 
    regex_keywords: List[str]
    spacy_keywords: List[str]
    gazetteer_keywords: List[str]
    llm_keywords: List[str]
    union_list: List[str]
    
    keywords: List[str] # Final keywords produced by the Tag Generation Graph
    final_output: Dict[str, Union[str, List, Dict]]

    review_report: str  # Review report from Reviewer Agent

# --- 3. Build the Master Assembly Line Graph ---

def build_assembly_line_graph():
    """
    Builds and compiles the master LangGraph that chains the two sub-graphs.
    """
    print("--- 🏭 Building Master Assembly Line Graph ---")

    # Initialize the master StateGraph with the unified state
    workflow = StateGraph(UnifiedAnalysisState)
    
    # Get the compiled sub-graphs (they are the executables for the nodes)
    repo_analyzer_app = build_analyzer_graph()
    tag_generator_app = build_tag_generation_graph()
    meta_seo_app = build_meta_seo_graph()
    reviewer_app = build_reviewer_graph()

    # 3a. Add the compiled sub-graphs as nodes in the master workflow
    # LangGraph allows you to use a CompiledGraph (or any Runnable) as a node.
    workflow.add_node("repo_analyzer_node", repo_analyzer_app)
    workflow.add_node("tag_generator_node", tag_generator_app)
    workflow.add_node("meta_seo_node", meta_seo_app)
    workflow.add_node("reviewer_node", reviewer_app)
    # 3b. Define the workflow flow
    
    # Set the entry point to the first sub-graph
    workflow.set_entry_point("repo_analyzer_node")

    # Connect the first sub-graph to the second. 
    # The full state output of 'repo_analyzer_node' automatically becomes 
    # the input for 'tag_generator_node'.
    workflow.add_edge("repo_analyzer_node", "tag_generator_node")
    workflow.add_edge("tag_generator_node", "meta_seo_node")
    workflow.add_edge("meta_seo_node", "reviewer_node")
    
    # Connect the second sub-graph to the end
    workflow.add_edge("reviewer_node", END)

    # 3c. Compile the master graph
    app = workflow.compile()
    print("✅ Master Assembly Line Graph Compiled.")
    return app


def run_assembly_line_analysis(repo_url: str) -> Dict[str, Any]:
    """
    Executes the unified assembly line LangGraph.
    """
    
    # Build the unified graph
    assembly_line_app = build_assembly_line_graph()
    
    initial_state: Dict[str, Any] = {"repo_url": repo_url}

    print(f"\n--- 🚀 Executing Assembly Line for: {repo_url} ---")
    
    # Invoke the single master graph
    # This single call runs the state from start to finish (Analyzer -> Tag Generator -> END)
    final_state: UnifiedAnalysisState = assembly_line_app.invoke(initial_state)

    print("✅ Assembly Line Complete.")

    # ----------------------------------------------------------------
    # FINAL ASSEMBLY (using the final state of the master graph)
    # ----------------------------------------------------------------
    
    # Extract data from the final state produced by the entire graph run
    final_result = {
        "project_summary": final_state.get("summaries", {}).get("readme.md", "No README available"),
        "file_summaries": final_state.get("summaries"),
        "missing_documentation": final_state.get("missing_docs"),
        "keywords": final_state.get("keywords", []),
        "file_structure": final_state.get("final_output", {}).get("file_structure", {}),
        "suggested_tags": final_state.get("keywords", [])[:5],
        "short_summary": final_state.get("short_summary", ""),
        "long_summary": final_state.get("long_summary", ""),
        "suggested_title": final_state.get("suggested_title", ""),
        "github_topics": final_state.get("github_topics", []),
        "review_report": final_state.get("review_report", ""),
    }
    
    return final_result

# ----------------------------------------------------------------
# Main Execution Block
# ----------------------------------------------------------------
if __name__ == "__main__":
    
    # NOTE: Ensure the GROQ_API_KEY environment variable is set.
    
    repo_to_analyze = "https://github.com/roshan9419/LearnEd_E-learning_Website"
    
    try:
        final_analysis = run_assembly_line_analysis(repo_to_analyze)
        
        print("\n\n=============== FINAL REPORT ===============")
        # Use simple string formatting for better readability of the print statements
        print(json.dumps(final_analysis, indent=2))
        print("============================================")

    except Exception as e:
        # NOTE: In a real environment, you should replace 'CompiledGraph' 
        # with the actual imported type from LangGraph.
        print(f"\n❌ An error occurred during the assembly line execution: {e}")