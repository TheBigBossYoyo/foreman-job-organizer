import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .dates import ground_dates
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import JobOrganizationResult

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class JobOrganizerError(RuntimeError):
    """Raised when the model call fails or its output can't be trusted."""


def extract_json_object(text):
    """Pull the JSON object out of a model reply.

    Most of the time the reply is clean JSON, but it sometimes arrives wrapped
    in a markdown fence or with a sentence in front of it, so we slice between
    the outer braces rather than parsing the whole reply.
    """
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        raise JobOrganizerError("The model response did not contain a JSON object.")

    try:
        parsed = json.loads(text[first:last + 1])
    except json.JSONDecodeError as exc:
        raise JobOrganizerError(f"Invalid JSON returned by the model: {exc}")

    if not isinstance(parsed, dict):
        raise JobOrganizerError("The model returned JSON, but not a JSON object.")
    return parsed


def call_groq(raw_text, model=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise JobOrganizerError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    from groq import Groq

    client = Groq(api_key=api_key)

    # temperature=0 so the same sample gives the same answer twice. Without it
    # our accuracy score would move around between runs for no real reason.
    try:
        response = client.chat.completions.create(
            model=model or os.getenv("GROQ_MODEL", DEFAULT_MODEL),
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(raw_text)},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise JobOrganizerError(f"Groq API call failed: {exc}")

    content = response.choices[0].message.content
    if not content:
        raise JobOrganizerError("Groq returned an empty response.")
    return content


def organize_job_stream(raw_text, model=None):
    """Turn one messy job stream into a validated result. This is the core function."""
    if not raw_text or not raw_text.strip():
        raise ValueError("Input text cannot be empty.")

    parsed = extract_json_object(call_groq(raw_text, model))

    # JSON can be well formed and still be wrong for us: an invented category,
    # a negative amount, a missing summary. Check it before anyone uses it.
    try:
        result = JobOrganizationResult.model_validate(parsed)
    except ValidationError as exc:
        raise JobOrganizerError(f"Output validation failed:\n{exc}")

    # Validation only proves the shape is right. A date can pass every check
    # here and still have been copied off a neighbouring line, so drop the ones
    # the item does not actually say.
    return ground_dates(result)


def save_result(result, path):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ensure_ascii=False keeps accented names and currency symbols readable.
    output_path.write_text(
        json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
