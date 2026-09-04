from fastapi import APIRouter, HTTPException
from models.schemas import CodeRequest, ExplainResponse
from services.llm_client import explain_code

router = APIRouter()

# Simple in-memory cache: same snippet -> skip LLM call
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    _cache[cache_key] = result
    return result
