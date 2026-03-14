from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from app.analyzers.ast_analyzer import ASTAnalyzer
from app.analyzers.llm_analyzer import LLMAnalyzer
from app.analyzers.call_graph import CallGraphBuilder
from app.analyzers.cross_file_analyzer import CrossFileAnalyzer
import json

router = APIRouter()

class CodeRequest(BaseModel):
    code: str
    language: str = "python"

class MultiFileRequest(BaseModel):
    files: List[dict]
    language: str = "python"

@router.post("/analyze")
async def analyze_code(request: CodeRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    ast_analyzer = ASTAnalyzer(request.code, request.language)
    ast_result = ast_analyzer.analyze()

    if "error" in ast_result:
        raise HTTPException(status_code=400, detail=ast_result["error"])

    llm_analyzer = LLMAnalyzer()
    explained_items = llm_analyzer.explain_dead_code(
        request.code,
        ast_result["dead_code_items"]
    )

    call_graph = CallGraphBuilder(request.code, request.language)
    graph_data = call_graph.build()

    return {
        "success": True,
        "language": request.language,
        "total_lines": ast_result["total_lines"],
        "dead_count": ast_result["dead_count"],
        "summary": ast_result["summary"],
        "dead_code_items": explained_items,
        "call_graph": graph_data,
        "defined_functions": ast_result["defined_functions"],
        "called_functions": ast_result["called_functions"]
    }

@router.post("/analyze-project")
async def analyze_project(request: MultiFileRequest):
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    analyzer = CrossFileAnalyzer()

    for file in request.files:
        filename = file.get("filename", "unknown.py")
        code = file.get("code", "")
        if code.strip():
            analyzer.add_file(filename, code)

    if not analyzer.files:
        raise HTTPException(status_code=400, detail="No valid files to analyze")

    result = analyzer.analyze_all()

    # Get AI explanations for dead code
    all_code = "\n".join(analyzer.files.values())
    llm_analyzer = LLMAnalyzer()
    explained_items = llm_analyzer.explain_dead_code(
        all_code,
        result["dead_code_items"]
    )
    result["dead_code_items"] = explained_items

    return result

@router.get("/health")
def health():
    import sys
    return {
        "status": "ok",
        "message": "Backend is running",
        "python_version": sys.version,
        "supported_languages": ["python", "javascript"],
        "features": ["ast_analysis", "llm_explanation", "call_graph", "websocket", "cross_file_analysis"]
    }