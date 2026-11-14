import logging

from fastapi import APIRouter, HTTPException
from models.schemas import CodeRequest, ExplainResponse
from services.llm_client import explain_code

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory cache: same snippet -> skip LLM call.
# Bounded so a long-running server cannot grow memory without limit.
MAX_CACHE_ENTRIES = 500
_cache: dict[str, dict] = {}


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: CodeRequest):
    cache_key = f"{req.language_hint}:{req.code}"

    if cache_key in _cache:
        return _cache[cache_key]

    try:
        result = await explain_code(req.code, req.language_hint)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        logger.exception("Unexpected error while explaining code")
        raise HTTPException(status_code=500, detail="Unexpected error while explaining code")

    if len(_cache) >= MAX_CACHE_ENTRIES:
        _cache.clear()
    _cache[cache_key] = result
    return result
