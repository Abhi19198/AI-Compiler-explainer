# 🧠 AI Code Explainer

> Paste a code snippet and get a professional breakdown: a line-by-line explanation, time/space complexity, a dry run, a Mermaid flowchart, and bug/improvement suggestions — powered by Claude.

## 🚀 Overview

**AI Code Explainer** is a small web app for students and developers who want to understand unfamiliar code quickly.

Instead of just showing what code does, it explains it piece by piece: what each line means, how expensive it is, how it executes step by step, and what could go wrong with it.

Given a snippet, it returns:

- **Line-by-line explanation** — each line in plain language
- **Time & space complexity** — Big-O with reasoning
- **Dry run** — a worked example with variable states and final output
- **Flowchart** — a Mermaid.js diagram of the control flow
- **Bugs & suggestions** — issues found, with severity and fixes
- **Summary** — a 2–3 line overview of what the code does

## 🧱 How it works

```text
Code snippet (any language)
     │
     ▼
FastAPI backend (POST /explain)
     │
     ▼
Claude API (structured JSON response)
     │
     ▼
Single-page frontend — summary, complexity,
line-by-line trace, flowchart, dry run, review notes
```

## 📁 Project layout

```text
ai-code-explainer/
├── backend/        # FastAPI app (see its README for setup)
└── frontend/       # Single-file HTML/JS UI, no build step
```

Full setup, API docs and next steps: [`ai-code-explainer/README.md`](ai-code-explainer/README.md).

## ⚡ Quick start

```bash
cd ai-code-explainer/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000
```

```bash
cd ai-code-explainer/frontend
python -m http.server 5500
# open http://localhost:5500
```

Or run the backend in Docker (key passed at runtime, never baked in):

```bash
docker build -t ai-code-explainer .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... ai-code-explainer
```

## ✅ Tests

```bash
cd ai-code-explainer/backend
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests stub the Claude call, so they run with no API key and no network. A live explanation needs a real `ANTHROPIC_API_KEY`.

## License

MIT — see [LICENSE](LICENSE).
