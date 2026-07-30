from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from .demo_mode import organize_without_ai
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import JobOrganizationResult

load_dotenv()


class JobOrganizerError(RuntimeError):
    pass


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract one JSON object even if a model adds surrounding text."""
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        raise JobOrganizerError("The model response did not contain a JSON object.")

    candidate = text[first : last + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise JobOrganizerError(f"Invalid JSON returned by the model: {exc}") from exc

    if not isinstance(parsed, dict):
        raise JobOrganizerError("The model returned JSON, but not a JSON object.")
    return parsed


def _call_groq(raw_text: str, model: str | None = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise JobOrganizerError("GROQ_API_KEY is not configured.")

    try:
        from groq import Groq
    except ImportError as exc:
        raise JobOrganizerError(
            "The groq package is missing. Run: pip install -r requirements.txt"
        ) from exc

    chosen_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=chosen_model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(raw_text)},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise JobOrganizerError(f"Groq API call failed: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise JobOrganizerError("Groq returned an empty response.")
    return content


def organize_job_stream(
    raw_text: str,
    *,
    demo_mode: bool | None = None,
    model: str | None = None,
) -> JobOrganizationResult:
    """Convert messy contractor updates into validated structured output.

    When demo_mode is None, the function automatically uses demo mode if no
    GROQ_API_KEY exists. Pass demo_mode=False to require a real Groq call.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Input text cannot be empty.")

    use_demo = demo_mode if demo_mode is not None else not bool(os.getenv("GROQ_API_KEY"))

    raw_result = (
        organize_without_ai(raw_text)
        if use_demo
        else _extract_json_object(_call_groq(raw_text, model=model))
    )

    try:
        return JobOrganizationResult.model_validate(raw_result)
    except ValidationError as exc:
        raise JobOrganizerError(f"Output validation failed:\n{exc}") from exc


def save_result(result: JobOrganizationResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
