from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.analyzers.ast_analyzer import ASTAnalyzer
from app.analyzers.call_graph import CallGraphBuilder
import json

router = APIRouter()

@router.websocket("/analyze")
async def websocket_analyze(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            code = payload.get("code", "")
            language = payload.get("language", "python")

            if not code.strip():
                await websocket.send_json({"dead_code_items": [], "dead_count": 0})
                continue

            # Fast AST analysis (no LLM for real-time)
            analyzer = ASTAnalyzer(code, language)
            result = analyzer.analyze()

            call_graph = CallGraphBuilder(code, language)
            graph = call_graph.build()

            await websocket.send_json({
                "dead_count": result.get("dead_count", 0),
                "dead_code_items": result.get("dead_code_items", []),
                "call_graph": graph,
                "summary": result.get("summary", {})
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})