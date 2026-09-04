import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers.explain import router as explain_router

app = FastAPI(
    title="AI Code Explainer API",
    description="Paste code, get line-by-line explanation, complexity, flowchart, dry run, and bug suggestions.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,null").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(explain_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
