import os
import json
from typing import Dict, Any, List, TypedDict, Union
from langgraph.graph import StateGraph, END

# --- 1. Import the Graph Builders from their respective locations ---
from Agents.RepoAnalyzerAgent.RepoAnalyzer import build_analyzer_graph
from Agents.MetaDataAgent.Graph._Tagsgraph import build_tag_generation_graph
from Agents.MetaDataAgent.Graph._MetaSEOGraph import build_meta_seo_graph
from Agents.Reviewer.__graph__ import build_reviewer_graph

class UnifiedAnalysisState(TypedDict):
    #Fields for Entire Assembly Line
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    files_structure: Dict[str, Any]
    readme_md: str
    missing_docs: List[str]
    github_keywords_extracted: List[str]

    suggested_title: str         
    short_summary: str           
    long_summary: str            
    github_topics: List[str]     

    content_text: str 
    regex_keywords: List[str]
    spacy_keywords: List[str]
    gazetteer_keywords: List[str]
    llm_keywords: List[str]
    union_list: List[str]
    
    keywords: List[str]

    review_report: str 

def build_assembly_line_graph():
    """
    Builds and compiles the master LangGraph that chains the sub-graphs.
    """
    print("--- 🏭 Building Master Assembly Line Graph ---")

    # Initialize the master StateGraph with the unified state
    workflow = StateGraph(UnifiedAnalysisState)
    
    repo_analyzer_app = build_analyzer_graph()
    tag_generator_app = build_tag_generation_graph()
    meta_seo_app = build_meta_seo_graph()
    reviewer_app = build_reviewer_graph()


    workflow.add_node("repo_analyzer_node", repo_analyzer_app)
    workflow.add_node("tag_generator_node", tag_generator_app)
    workflow.add_node("meta_seo_node", meta_seo_app)
    workflow.add_node("reviewer_node", reviewer_app)

    # 3b. Define the workflow flow
    
    workflow.set_entry_point("repo_analyzer_node")

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
    
    final_state: UnifiedAnalysisState = assembly_line_app.invoke(initial_state)

    print("✅ Assembly Line Complete.")
    
    # Extract data from the final state produced by the entire graph run
    final_result = {
        "project_summary": final_state.get("readme_md", ""),
        "file_summaries": final_state.get("summaries"),
        "missing_documentation": final_state.get("missing_docs"),
        "keywords": final_state.get("keywords", []),
        "file_structure": final_state.get("files_structure", {}),
        "suggested_tags": final_state.get("keywords", [])[:5],
        "short_summary": final_state.get("short_summary", ""),
        "long_summary": final_state.get("long_summary", ""),
        "suggested_title": final_state.get("suggested_title", ""),
        "github_topics": final_state.get("github_topics", []),
        "review_report": final_state.get("review_report", ""),
        "github_keywords_extracted": final_state.get("github_keywords_extracted", []),
    }
    
    return final_result