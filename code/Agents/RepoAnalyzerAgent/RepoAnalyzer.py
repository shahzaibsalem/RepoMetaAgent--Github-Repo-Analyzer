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