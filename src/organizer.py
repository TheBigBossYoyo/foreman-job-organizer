import json
from pathlib import Path

from pydantic import ValidationError

from . import providers
from .dates import ground_dates
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import JobOrganizationResult


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


def organize_job_stream(raw_text, model=None):
    """Turn one messy job stream into a validated result. This is the core function.

    The provider chain decides who answers, and records which one did on the
    result. Temperature is 0 wherever it is supported, so the same sample gives
    the same answer twice and the accuracy number does not drift between runs.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Input text cannot be empty.")

    try:
        reply, provider = providers.complete(
            SYSTEM_PROMPT, build_user_prompt(raw_text), raw_text, model
        )
    except providers.ProviderError as exc:
        raise JobOrganizerError(str(exc))

    parsed = extract_json_object(reply)

    # JSON can be well formed and still be wrong for us: an invented category,
    # a negative amount, a missing summary. Check it before anyone uses it.
    try:
        result = JobOrganizationResult.model_validate(parsed)
    except ValidationError as exc:
        raise JobOrganizerError(f"Output validation failed:\n{exc}")

    result.provider = provider

    # Validation only proves the shape is right. A date can pass every check
    # here and still have been copied off a neighbouring line, so compare each
    # one against the line it came from and drop the ones that are not there.
    return ground_dates(result, raw_text)


def save_result(result, path):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ensure_ascii=False keeps accented names and currency symbols readable.
    output_path.write_text(
        json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
