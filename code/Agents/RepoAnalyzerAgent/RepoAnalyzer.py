import os
import re
import json
import requests
from collections import Counter
from typing import TypedDict, List, Dict, Union

from langgraph.graph import StateGraph, END

class AnalysisState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    readme_md: str
    missing_docs: List[str]
    keywords: List[str]
    github_keywords_extracted: List[str]
    final_output: Dict[str, Union[str, List, Dict]]

# -----------------------------------------
# ---------- GitHub File Fetcher ----------
# -----------------------------------------
def fetch_files_node(state: AnalysisState) -> AnalysisState:
    """
    Fetch ALL files from GitHub repository recursively.
    """

    repo_url = state["repo_url"].rstrip("/")
    user, repo = repo_url.split("/")[-2:]

    base_api = f"https://api.github.com/repos/{user}/{repo}/contents"

    def fetch_dir(url, path=""):
        items = []
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data:
            full_path = f"{path}/{item['name']}".lstrip("/")

            if item["type"] == "file":
                items.append({
                    "name": item["name"],
                    "path": full_path,
                    "download_url": item.get("download_url")
                })

            elif item["type"] == "dir":
                items.append({
                    "name": item["name"],
                    "path": full_path,
                    "children": fetch_dir(item["url"], full_path)
                })

        return items

    print("✓ Fetching GitHub repository files (recursive)...")
    file_structure = fetch_dir(base_api)
    return {"files": file_structure}

# -----------------------------------------
# ---------- Documentation Checker --------
# -----------------------------------------
def doc_checker_node(state: AnalysisState) -> AnalysisState:
    """Case-insensitive check for README, LICENSE, CONTRIBUTING, COC."""

    REQUIRED = [
        "readme.md",
        "license",
        "contributing.md",
        "code_of_conduct.md"
    ]

    def flatten(files):
        result = []
        for f in files:
            if "children" in f:
                result.extend(flatten(f["children"]))
            else:
                result.append(f["name"].lower())
        return result

    filenames = flatten(state["files"])
    missing = []

    for req in REQUIRED:
        if not any(req in f for f in filenames):
            missing.append(req)

    print("✓ Checking documentation files...")
    return {"missing_docs": missing}

# -----------------------------------------
# ---------- Keyword Extractor ------------
# -----------------------------------------
def keyword_extractor_node(state: AnalysisState) -> AnalysisState:
    """Extract GitHub repo topics."""

    repo_url = state["repo_url"].rstrip("/")
    user, repo = repo_url.split("/")[-2:]

    api_url = f"https://api.github.com/repos/{user}/{repo}"

    print("✓ Fetching GitHub repository topics...")

    try:
        response = requests.get(api_url, headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()

        data = response.json()
        topics = data.get("topics", [])
    except Exception as e:
        topics = []
        print("Error fetching topics:", e)

    print("✓ Extracted repository topics.")
    print(f"Topics found: {topics}")    

    return {"github_keywords_extracted": topics}

# -----------------------------------------
# ---------- README Extractor --------------
# -----------------------------------------
def readme_extractor_node(state: AnalysisState) -> AnalysisState:
    """
    Extract ONLY README.md content.
    DO NOT summarize other files.
    """

    def flat(files):
        out = []
        for f in files:
            if "children" in f:
                out.extend(flat(f["children"]))
            else:
                out.append(f)
        return out

    file_list = flat(state["files"])

    readme_content = None

    for f in file_list:
        if f["name"].lower() == "readme.md":
            try:
                readme_content = requests.get(f["download_url"]).text
            except:
                readme_content = "Error fetching README.md"
            break

    print("✓ Extracted README.md raw content.")

    return {
        "readme_md": readme_content or "No README.md found",
        "summaries": {} 
    }

# -----------------------------------------
# ---------- Final Formatter --------------
# -----------------------------------------
def final_formatter_node(state: AnalysisState) -> AnalysisState:
    """Combine everything into one final JSON output."""

    def build_tree(files):
        tree = {}
        for f in files:
            if "children" in f:
                tree[f["name"]] = build_tree(f["children"])
            else:
                tree[f["name"]] = "file"
        return tree
    
    file_structure = build_tree(state["files"])


    print("✓ Creating final report...")
    return { "files_structure": file_structure }

def build_analyzer_graph():
    
    """
    Builds and compiles the Repo Analyzer LangGraph.
    """

    workflow = StateGraph(AnalysisState)

    workflow.add_node("fetcher", fetch_files_node)
    workflow.add_node("checker", doc_checker_node)
    workflow.add_node("extractor", keyword_extractor_node)
    workflow.add_node("readme", readme_extractor_node)
    workflow.add_node("formatter", final_formatter_node)

    workflow.set_entry_point("fetcher")
    workflow.add_edge("fetcher", "checker")
    workflow.add_edge("checker", "extractor")
    workflow.add_edge("extractor", "readme")
    workflow.add_edge("readme", "formatter")
    workflow.add_edge("formatter", END)

    return workflow.compile()
