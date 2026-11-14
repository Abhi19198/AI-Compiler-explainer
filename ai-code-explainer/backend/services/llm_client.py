import json
import os
import re

from anthropic import AsyncAnthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# anthropic 0.34.2 passes `proxies` to httpx, which httpx 0.28 removed, so
# requirements.txt pins httpx==0.27.2. Keep the client lazy as well: building
# it at import time used to crash the whole app when ANTHROPIC_API_KEY was
# unset, before any request was served.
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=60.0,
        )
    return _client


SYSTEM_PROMPT = """You are an expert Senior Software Engineer and Code Reviewer AI assistant integrated into a developer tool called "AI Code Explainer".

Your job: given a code snippet (any language), analyze it and return a structured, professional explanation.

STRICT OUTPUT FORMAT (return valid JSON only, no markdown fences, no extra text):

{
  "language_detected": "string",
  "line_by_line_explanation": [
    {"line": "code line", "explanation": "plain-language explanation"}
  ],
  "time_complexity": {
    "value": "Big-O notation, e.g. O(n)",
    "reasoning": "short explanation of why"
  },
  "space_complexity": {
    "value": "Big-O notation",
    "reasoning": "short explanation of why"
  },
  "dry_run": {
    "sample_input": "example input used",
    "steps": [
      {"step": 1, "state": "variable values at this point", "note": "what happened"}
    ],
    "final_output": "resulting value/output"
  },
  "flowchart_mermaid": "valid Mermaid.js flowchart syntax as a string",
  "bugs_and_suggestions": [
    {"severity": "low|medium|high", "issue": "description", "suggestion": "how to fix"}
  ],
  "summary": "2-3 line plain-English summary of what the code does overall"
}

RULES:
- Always produce valid Mermaid flowchart syntax (flowchart TD ...).
- If code has a bug (e.g. off-by-one, missing bounds check, uninitialized variable), you MUST flag it under bugs_and_suggestions.
- Keep explanations beginner-friendly but technically accurate.
- If time/space complexity depends on unclear factors (e.g. recursion depth), state assumptions clearly.
- Do not hallucinate behavior not present in the code.
- If the snippet is incomplete or has a syntax error, note this in "bugs_and_suggestions" but still attempt best-effort analysis.
- Return ONLY the JSON object. No markdown code fences, no preamble, no commentary.
"""


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


async def explain_code(code: str, language_hint: str | None = None) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError(
            "ANTHROPIC_API_KEY is missing. Add it to backend/.env and restart the server."
        )

    user_message = f"Language hint: {language_hint or 'unknown'}\n\nCode:\n```\n{code}\n```"

    response = await _get_client().messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    cleaned = _strip_json_fences(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}\nRaw output: {raw_text[:500]}")
