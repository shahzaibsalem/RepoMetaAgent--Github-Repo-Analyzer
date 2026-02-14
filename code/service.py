from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
import traceback
from assembly_line import run_assembly_line_analysis


app = FastAPI(
    title="RepoMetaAgent API",
    description="Analyze a GitHub repository and return structured metadata",
    version="1.0.0"
)


# -------- Request Schema --------

class RepoRequest(BaseModel):
    repo_url: HttpUrl


# -------- Response Schema (Optional but Recommended) --------

class RepoResponse(BaseModel):
    project_summary: str
    missing_documentation: list
    keywords: list
    github_keywords_extracted: list
    suggested_tags: list
    suggested_title: str
    github_topics: list
    short_summary: str
    long_summary: str
    review_report: str
    file_structure: Dict[str, Any]


# -------- Health Check --------

@app.get("/")
def health():
    return {"status": "RepoMetaAgent API running"}


# -------- Main Endpoint --------

@app.post("/analyze", response_model=RepoResponse)
def analyze_repo(payload: RepoRequest):
    try:
        result = run_assembly_line_analysis(payload.repo_url)
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
