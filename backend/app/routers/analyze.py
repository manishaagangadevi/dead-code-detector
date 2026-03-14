from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.analyzers.ast_analyzer import ASTAnalyzer
from app.analyzers.llm_analyzer import LLMAnalyzer
from app.analyzers.call_graph import CallGraphBuilder

router = APIRouter()

class CodeRequest(BaseModel):
    code: str
    language: str = "python"

@router.post("/analyze")
async def analyze_code(request: CodeRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Step 1 — AST Analysis
    ast_analyzer = ASTAnalyzer(request.code, request.language)
    ast_result = ast_analyzer.analyze()

    if "error" in ast_result:
        raise HTTPException(status_code=400, detail=ast_result["error"])

    # Step 2 — LLM Explanation
    llm_analyzer = LLMAnalyzer()
    explained_items = llm_analyzer.explain_dead_code(
        request.code,
        ast_result["dead_code_items"]
    )

    # Step 3 — Call Graph
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

@router.get("/health")
def health():
    return {"status": "ok", "message": "Backend is running"}