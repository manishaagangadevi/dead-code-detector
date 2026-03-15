<div align="center">

# 🔍 Dead Code Detector

### AI-Powered Static Analysis Tool for Python & JavaScript

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://reactjs.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA3-F54642?style=for-the-badge)](https://groq.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Detect unused functions, dead variables, and unreachable code blocks across your entire codebase — with AI-powered explanations and fix suggestions.*

[Features](#-features) • [Tech Stack](#-tech-stack) • [Setup](#-setup) • [Usage](#-usage) • [API Docs](#-api-reference)

</div>

---

## 🚀 What is Dead Code Detector?

**Dead Code Detector** is a full-stack AI-powered static analysis tool that goes beyond simple linting. It parses your code into an Abstract Syntax Tree (AST), builds a cross-file call graph, and uses a Large Language Model (LLM) to explain *why* each piece of code is dead and *how* to fix it.

Unlike basic linters, this tool:
- Analyzes **multiple files together** — a function used in `main.py` but defined in `utils.py` is correctly identified as **alive**
- Uses **AI to explain** dead code in plain English, not just flag line numbers
- Visualizes your entire **function call graph** interactively
- Provides **real-time analysis** as you type via WebSocket

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Explanations** | Groq LLaMA3 explains why each dead code block exists and how to fix it |
| 🌐 **Cross-File Analysis** | Upload entire projects — detects functions unused across ALL files |
| 📊 **Interactive Call Graph** | Force-directed graph showing function relationships with dead nodes highlighted in red |
| ⚡ **Live WebSocket Analysis** | Real-time dead code detection as you type in the editor |
| 🎨 **Monaco Editor** | VS Code's editor embedded in the browser with syntax highlighting |
| 📄 **PDF Export** | Generate professional dark-themed reports with AI explanations |
| 🐍 **Multi-Language** | Full support for Python and JavaScript/TypeScript |
| 📁 **File Upload** | Upload single files or entire project folders |
| 💊 **Health Score** | Codebase health percentage based on dead code ratio |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | High-performance REST API and WebSocket server |
| **Python AST** | Built-in Python abstract syntax tree parser |
| **Esprima** | JavaScript AST parser for JS/TS analysis |
| **Groq (LLaMA 3.3-70B)** | Free LLM API for AI-powered code explanations |
| **Uvicorn** | ASGI server for async request handling |
| **WebSockets** | Real-time bidirectional communication |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | Component-based UI framework |
| **Vite** | Lightning-fast build tool and dev server |
| **Monaco Editor** | VS Code's editor for in-browser code editing |
| **Cytoscape.js** | Interactive call graph visualization |
| **Axios** | HTTP client for API communication |
| **jsPDF** | Client-side PDF generation |
| **Lucide React** | Modern icon library |

---

## 📁 Project Structure

```
dead-code-detector/
├── backend/
│   ├── app/
│   │   ├── analyzers/
│   │   │   ├── ast_analyzer.py        # Python & JS AST analysis
│   │   │   ├── llm_analyzer.py        # Groq LLM integration
│   │   │   ├── call_graph.py          # Call graph builder
│   │   │   └── cross_file_analyzer.py # Multi-file analysis engine
│   │   ├── routers/
│   │   │   ├── analyze.py             # REST API endpoints
│   │   │   └── websocket.py           # WebSocket endpoint
│   │   └── main.py                    # FastAPI app entry point
│   ├── .env                           # Environment variables (not committed)
│   ├── .env.example                   # Example environment file
│   └── requirements.txt               # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Main React component
│   │   ├── main.jsx                   # React entry point
│   │   └── index.css                  # Global dark theme styles
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/manishaagangadevi/dead-code-detector.git
cd dead-code-detector
```

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Add your Groq API key to .env
# GROQ_API_KEY=your_key_here

# Start the backend server
uvicorn app.main:app --reload
```
Backend will run at: `http://127.0.0.1:8000`

### 3. Frontend Setup
```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend will run at: `http://localhost:5173`

---

## 📖 Usage

### Single File Analysis
1. Open `http://localhost:5173`
2. Paste your Python or JavaScript code in the editor
3. Select the language from the dropdown
4. Click **Analyze**
5. View issues, call graph, and AI explanations in the right panel

### Multi-File Project Analysis
1. Click **Upload Project** button
2. Select multiple `.py` or `.js` files from your project
3. Click **Analyze**
4. The tool will analyze all files together — functions used across files are correctly identified as alive

### Export Report
After analysis, click **Export PDF** to download a detailed dark-themed report including:
- Summary statistics
- All dead code issues with line numbers
- AI explanations for each issue
- Fix suggestions

---

## 🔌 API Reference

### `POST /api/analyze`
Analyze a single file for dead code.

**Request:**
```json
{
  "code": "def unused_func():\n    pass\n",
  "language": "python"
}
```

**Response:**
```json
{
  "success": true,
  "language": "python",
  "total_lines": 2,
  "dead_count": 1,
  "dead_code_items": [
    {
      "type": "dead_function",
      "name": "unused_func",
      "line_start": 1,
      "line_end": 2,
      "severity": "high",
      "message": "Function 'unused_func' is defined but never called",
      "ai_explanation": "...",
      "fix_suggestion": "..."
    }
  ],
  "call_graph": { "nodes": [], "edges": [] },
  "summary": {
    "dead_functions": 1,
    "dead_variables": 0,
    "unreachable_blocks": 0
  }
}
```

### `POST /api/analyze-project`
Analyze multiple files together with cross-file awareness.

**Request:**
```json
{
  "files": [
    { "filename": "main.py", "code": "..." },
    { "filename": "utils.py", "code": "..." }
  ],
  "language": "python"
}
```

### `GET /api/health`
Health check endpoint.

### `WS /ws/analyze`
WebSocket endpoint for real-time analysis. Send JSON:
```json
{ "code": "...", "language": "python" }
```

Full interactive API documentation available at `http://127.0.0.1:8000/docs`

---

## 🧠 How It Works

```
Code Input
    │
    ▼
AST Parser (Python AST / Esprima)
    │
    ▼
Symbol Table Builder
├── Collect all defined functions
├── Collect all defined variables
└── Collect all function calls & usages
    │
    ▼
Cross-File Reference Resolver
├── Build global symbol table across all files
├── Resolve imports and exports
└── Mark functions used in any file as alive
    │
    ▼
Dead Code Detector
├── Functions defined but never called = dead
├── Variables assigned but never used = dead
└── Code after return statements = unreachable
    │
    ▼
LLM Analyzer (Groq LLaMA 3.3-70B)
├── Explain why each block is dead
└── Suggest specific fixes
    │
    ▼
Call Graph Builder
└── Visualize function relationships
    │
    ▼
Results (UI + PDF Export)
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Manisha Gangadevi**

---

<div align="center">

Made with ❤️ for the love of clean code

⭐ Star this repo if you found it helpful!

</div>
