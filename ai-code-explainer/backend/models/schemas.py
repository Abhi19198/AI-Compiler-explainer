from pydantic import BaseModel, Field
from typing import Optional, List


class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=8000, description="Source code snippet to analyze")
    language_hint: Optional[str] = Field(None, description="Optional hint like 'python', 'java', 'cpp'")


class LineExplanation(BaseModel):
    line: str
    explanation: str


class ComplexityInfo(BaseModel):
    value: str
    reasoning: str


class DryRunStep(BaseModel):
    step: int
    state: str
    note: str


class DryRun(BaseModel):
    sample_input: str
    steps: List[DryRunStep]
    final_output: str


class BugSuggestion(BaseModel):
    severity: str
    issue: str
    suggestion: str


class ExplainResponse(BaseModel):
    language_detected: str
    line_by_line_explanation: List[LineExplanation]
    time_complexity: ComplexityInfo
    space_complexity: ComplexityInfo
    dry_run: DryRun
    flowchart_mermaid: str
    bugs_and_suggestions: List[BugSuggestion]
    summary: str
