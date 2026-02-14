from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
import traceback
from assembly_line import run_assembly_line_analysis


app = FastAPI(
    title="RepoMetaAgent API",
    description="Analyze a GitHub repository and return structured metadata",
    version="1.0.0"
)


class RepoRequest(BaseModel):
    repo_url: HttpUrl


@app.get("/")
def health():
    return {"status": "RepoMetaAgent API running"}


@app.post("/analyze")
async def analyze_repo(payload: RepoRequest):
    try:
        result = await run_in_threadpool(
            run_assembly_line_analysis,
            str(payload.repo_url)   # 🔥 THIS IS THE FIX
        )
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
