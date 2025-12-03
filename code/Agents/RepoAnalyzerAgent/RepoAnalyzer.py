# import os
# import re
# import json
# import requests
# from collections import Counter
# from groq import Groq
# from typing import TypedDict, List, Dict, Union

# # LangGraph imports
# from langgraph.graph import StateGraph, END
# from langgraph.graph.message import AnyMessage, Messages

# # ----------------------
# # Define the Graph State
# # ----------------------
# class AnalysisState(TypedDict):
#     """
#     Represents the state of the analysis, shared across all nodes.
#     """
#     repo_url: str
#     files: List[Dict]
#     summaries: Dict[str, str]
#     README_md: str
#     missing_docs: List[str]
#     keywords: List[str]
#     final_output: Dict[str, Union[str, List, Dict]]

# # ----------------------
# # GitHub Fetcher Tool (Node)
# # ----------------------
# def fetch_files_node(state: AnalysisState) -> AnalysisState:
#     """Fetch files from a GitHub repository using GitHub API (Node 1)."""
#     repo_url = state["repo_url"]
#     parts = repo_url.rstrip("/").split("/")
#     user, repo = parts[-2], parts[-1]
#     api_url = f"https://api.github.com/repos/{user}/{repo}/contents"

#     def _get_files(url):
#         response = requests.get(url)
#         response.raise_for_status()
#         items = response.json()
#         files = []
#         for item in items:
#             if item['type'] == 'file':
#                 files.append({"name": item['name'], "download_url": item['download_url']})
#             elif item['type'] == 'dir':
#                 files.append({"name": item['name'], "children": _get_files(item['url'])})
#         return files

#     print("--- 1. Fetching repository files...")
#     fetched_files = _get_files(api_url)
#     return {"files": fetched_files}

# # ----------------------
# # Doc Checker Tool (Node)
# # ----------------------
# def doc_checker_node(state: AnalysisState) -> AnalysisState:
#     """Check for required documentation files (Node 2)."""
#     files = state["files"]
#     REQUIRED_DOCS = ["README.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md"]

#     def _flatten_files(file_list):
#         names = []
#         for f in file_list:
#             if 'children' in f:
#                 names.extend(_flatten_files(f['children']))
#             else:
#                 names.append(f['name'])
#         return names

#     file_names = _flatten_files(files)
#     missing = [doc for doc in REQUIRED_DOCS if doc not in file_names]

#     print("--- 2. Checking for documentation...")
#     return {"missing_docs": missing}

# # ----------------------
# # Keyword Extractor Tool (Node)
# # ----------------------
# def keyword_extractor_node(state: AnalysisState) -> AnalysisState:
#     """Extract keywords from files (Node 3)."""
#     files = state["files"]
#     text = ""
#     for f in files:
#         if f['name'].endswith(('.md', '.py', '.js')):
#             try:
#                 # Assuming the file list is flat for simplicity, or fetching is recursive
#                 if 'download_url' in f:
#                     content = requests.get(f['download_url']).text
#                     text += content + " "
#             except:
#                 continue
    
#     words = re.findall(r'\b\w+\b', text.lower())
#     common = Counter(words).most_common(20)
#     keywords = [w for w, count in common if len(w) > 3]

#     print("--- 3. Extracting keywords...")
#     return {"keywords": keywords}

# # ----------------------
# # Code Summarizer Tool (Node)
# # ----------------------
# class CodeSummarizer:
#     """Wrapper for Groq API to summarize code."""
#     def __init__(self, model="llama-3.3-70b-versatile"):
#         api_key = os.getenv("GROQ_API_KEY")
#         self.client = Groq(api_key=api_key)
#         self.model = model

#     def summarize(self, files):
#         summaries = {}
#         for f in files:
#             # Only process files with a direct download link
#             if f.get('download_url') and f['name'].endswith(('.md', '.py', '.js', '.java')):
#                 try:
#                     content = requests.get(f['download_url']).text
#                     prompt = f"Summarize this file content in simple terms:\n\n{content}"

#                     response = self.client.chat.completions.create(
#                         model=self.model,
#                         messages=[{"role": "user", "content": prompt}]
#                     )
#                     summaries[f['name']] = response.choices[0].message.content
#                 except Exception as e:
#                     summaries[f['name']] = f"Error summarizing: {str(e)}"
#         return summaries

# SUMMARIZER = CodeSummarizer()

# def code_summarizer_node(state: AnalysisState) -> AnalysisState:
#     """Summarize README and code files using Groq API (Node 4)."""
#     files = state["files"]
#     print("--- 4. Summarizing files using Groq...")
    
#     # Flatten files to get only the items with download_url
#     def _flatten_files_for_summarization(file_list):
#         flat_files = []
#         for f in file_list:
#             if 'children' in f:
#                 flat_files.extend(_flatten_files_for_summarization(f['children']))
#             else:
#                 flat_files.append(f)
#         return flat_files

#     files_to_summarize = _flatten_files_for_summarization(files)
#     summaries = SUMMARIZER.summarize(files_to_summarize)
#     return {"summaries": summaries}

# # ----------------------
# # Final Formatter (Node)
# # ----------------------
# def final_formatter_node(state: AnalysisState) -> AnalysisState:
#     """Compile all results into the final output structure (Node 5)."""
    
#     def _get_file_structure(files):
#         structure = {}
#         for f in files:
#             if 'children' in f:
#                 structure[f['name']] = _get_file_structure(f['children'])
#             else:
#                 structure[f['name']] = "file"
#         return structure

#     files = state["files"]
#     summaries = state["summaries"]
#     missing_docs = state["missing_docs"]
#     keywords = state["keywords"]

#     output = {
#         "project_summary": summaries.get("README.md", "No README available"),
#         "file_summaries": summaries,
#         "missing_documentation": missing_docs,
#         "keywords": keywords,
#         "file_structure": _get_file_structure(files),
#         "suggested_tags": keywords[:5]
#     }
    
#     print("--- 5. Compiling final report...")
#     return {"final_output": output}

# # ----------------------
# # Build the LangGraph
# # ----------------------
# def build_analyzer_graph():
#     """Builds and compiles the sequential LangGraph."""
#     workflow = StateGraph(AnalysisState)

#     # Add Nodes
#     workflow.add_node("fetcher", fetch_files_node)
#     workflow.add_node("checker", doc_checker_node)
#     workflow.add_node("extractor", keyword_extractor_node)
#     workflow.add_node("summarizer", code_summarizer_node)
#     workflow.add_node("formatter", final_formatter_node)

#     # Define Edges
#     workflow.set_entry_point("fetcher")
#     workflow.add_edge("fetcher", "checker")        
#     workflow.add_edge("checker", "extractor")     
#     workflow.add_edge("extractor", "summarizer")    
#     workflow.add_edge("summarizer", "formatter")   
#     workflow.add_edge("formatter", END)        

#     return workflow.compile()


import os
import re
import json
import requests
from collections import Counter
from groq import Groq
from typing import TypedDict, List, Dict, Union

from langgraph.graph import StateGraph, END

# -----------------------------------------
# ---------- Graph State ------------------
# -----------------------------------------
class AnalysisState(TypedDict):
    repo_url: str
    files: List[Dict]
    summaries: Dict[str, str]
    readme_md: str
    missing_docs: List[str]
    keywords: List[str]
    final_output: Dict[str, Union[str, List, Dict]]

# -----------------------------------------
# ---------- GitHub File Fetcher ----------
# -----------------------------------------
def fetch_files_node(state: AnalysisState) -> AnalysisState:
    """
    Fetch ALL files from any GitHub repository recursively.
    Handles nested folders + pagination + returns clean full paths.
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

    print("✓ Checking documentation files (case insensitive)...")
    return {"missing_docs": missing}

# -----------------------------------------
# ---------- Keyword Extractor ------------
# -----------------------------------------
def keyword_extractor_node(state: AnalysisState) -> AnalysisState:
    """Extract meaningful keywords from ALL text/code files, recursively."""

    STOPWORDS = {
        "the", "and", "that", "with", "this", "from", "your", "have",
        "for", "you", "are", "was", "will", "use", "using", "when", "while"
    }

    def flatten(files):
        out = []
        for f in files:
            if "children" in f:
                out.extend(flatten(f["children"]))
            else:
                out.append(f)
        return out

    text = ""
    for f in flatten(state["files"]):
        if f.get("download_url"):
            try:
                content = requests.get(f["download_url"]).text
                if len(content) < 200_000:  # prevent large files
                    text += content + " "
            except:
                pass

    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]

    common = Counter(filtered).most_common(30)
    keywords = [w for w, _ in common]

    print("✓ Extracting keywords...")
    return {"keywords": keywords}

# -----------------------------------------
# ---------- Code Summarizer --------------
# -----------------------------------------
class CodeSummarizer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key)

    def summarize(self, files):
        summaries = {}

        for f in files:
            url = f.get("download_url")
            if not url:
                continue

            try:
                text = requests.get(url).text
                if len(text) > 35000:  # large files truncated
                    text = text[:35000]

                prompt = f"Summarize this file:\n\n{text}"

                resp = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )

                summaries[f["path"]] = resp.choices[0].message.content

            except Exception as e:
                summaries[f["path"]] = f"Error: {e}"

        return summaries


SUMMARIZER = CodeSummarizer()


def code_summarizer_node(state: AnalysisState) -> AnalysisState:
    """Summarize **all** files with download URLs."""

    def flat(files):
        arr = []
        for f in files:
            if "children" in f:
                arr.extend(flat(f["children"]))
            else:
                arr.append(f)
        return arr

    file_list = flat(state["files"])

    print("✓ Summarizing all code files...")
    summaries = SUMMARIZER.summarize(file_list)
    # Find any readme file inside summaries (case-insensitive)
    readme_summary = None
    for path, summary in summaries.items():
        if path.lower().endswith("readme.md"):
            readme_summary = summary
            break
    
    # state["readme_md"] = readme_summary or "No README detected"
    # teext = state.get("readme_md", "No README detected")
    # print("✓ Extracted README summary.")
    # print(teext)

    return {
     "summaries": summaries,
     "readme_md": readme_summary or "No README detected"
    }


# -----------------------------------------
# ---------- Final Formatter --------------
# -----------------------------------------
def final_formatter_node(state: AnalysisState) -> AnalysisState:
    """Combine everything into one structured JSON report."""

    def build_tree(files):
        tree = {}
        for f in files:
            if "children" in f:
                tree[f["name"]] = build_tree(f["children"])
            else:
                tree[f["name"]] = "file"
        return tree

    output = {
        "project_summary": state.get("readme_md", ""),
        "file_summaries": state["summaries"],
        "missing_documentation": state["missing_docs"],
        "keywords": state["keywords"],
        "file_structure": build_tree(state["files"]),
        "suggested_tags": state["keywords"][:7]
    }

    print("✓ Creating final report...")
    return {"final_output": output}

# -----------------------------------------
# ---------- Build Graph ------------------
# -----------------------------------------
def build_analyzer_graph():
    workflow = StateGraph(AnalysisState)

    workflow.add_node("fetcher", fetch_files_node)
    workflow.add_node("checker", doc_checker_node)
    workflow.add_node("extractor", keyword_extractor_node)
    workflow.add_node("summarizer", code_summarizer_node)
    workflow.add_node("formatter", final_formatter_node)

    workflow.set_entry_point("fetcher")
    workflow.add_edge("fetcher", "checker")
    workflow.add_edge("checker", "extractor")
    workflow.add_edge("extractor", "summarizer")
    workflow.add_edge("summarizer", "formatter")
    workflow.add_edge("formatter", END)

    return workflow.compile()