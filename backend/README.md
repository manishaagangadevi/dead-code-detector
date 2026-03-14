# Dead Code Detector - Backend

AI-powered dead code detection API built with FastAPI and Groq LLM.

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate`
3. Install deps: `pip install -r requirements.txt`
4. Add GROQ_API_KEY to .env file
5. Run: `uvicorn app.main:app --reload`

## API Endpoints
- POST /api/analyze - Analyze code for dead code
- GET /api/health - Health check
- WS /ws/analyze - WebSocket for live analysis

