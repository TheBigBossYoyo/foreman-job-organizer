"""Where the model call actually goes, and what happens when it cannot.

Three providers, tried in order:

1. **Anthropic** — the default when ANTHROPIC_API_KEY is set.
2. **Groq** — the backup. Used when Anthropic has no key, or when the Anthropic
   call raises. A demo should not die because one vendor is having a bad day.
3. **local** — a rule-based engine that needs no key at all. It returns the same
   JSON contract as the models, so the app still runs on a laptop with no
   network. It is visibly worse, and the scorer is what measures the gap.

Set AI_PROVIDER=anthropic|groq|local to pin one and skip the chain, which is
how the scorer measures a single engine at a time.
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Preference order. Anthropic leads; Groq covers for it; the local engine is
# the floor. resolve_chain drops whatever has no key, provider_status keeps
# them all so the reason can be shown.
PROVIDER_ORDER = ["anthropic", "groq", "local"]

HEADER_PATTERNS = [
    ("project_name", re.compile(r"^project\s*[:\-]\s*(.+)$", re.I)),
    ("client_name", re.compile(r"^client\s*(?:is|[:\-])\s*(.+)$", re.I)),
    ("property_address", re.compile(r"^address\s*[:\-]\s*(.+)$", re.I)),
]

# Order matters: the first rule that matches wins, so the specific categories
# have to come before the broad ones.
KEYWORD_RULES = [
    ("payment", ["invoice", "paid", "payment", "deposit", "draw "]),
    ("receipt", ["receipt", "bought", "purchased", "picked up", "supply house"]),
    ("photo", ["photo", ".jpg", ".png", "picture", "pic of"]),
    ("inspection", ["inspection", "inspector", "passed", "signed off"]),
    ("delivery", ["delivery", "delivered", "dropped off", "arrived", "dumpster"]),
    ("issue", ["problem", "issue", "rot", "leak", "damage", "moisture", "crack", "delay"]),
    ("schedule", ["reschedul", "pushing", "postpon", "move to", "rain date", "swing by"]),
    ("client_update", ["client", "homeowner", "owner", "texted", "emailed", "approved"]),
    ("contractor_update", ["crew", "demo", "framing", "install", "finished", "completed"]),
]

MONEY = re.compile(r"([$€£]|\b(?:TND|USD|EUR|GBP)\b)?\s*([0-9][0-9,]*(?:\.[0-9]{2})?)")
# The currency is written after the number about as often as before it.
CURRENCY_AFTER = re.compile(r"^\s*(TND|USD|EUR|GBP)\b", re.I)
CURRENCY_SIGNS = {"$": "USD", "€": "EUR", "£": "GBP"}


class ProviderError(RuntimeError):
    """Raised when every provider in the chain has failed."""


def resolve_chain():
    """The providers to try, in order, given the keys that are actually set."""
    forced = os.getenv("AI_PROVIDER", "").strip().lower()
    if forced in ("anthropic", "groq", "local"):
        return [forced]

    chain = []
    if os.getenv("ANTHROPIC_API_KEY"):
        chain.append("anthropic")
    if os.getenv("GROQ_API_KEY"):
        chain.append("groq")
    chain.append("local")
    return chain


def provider_status():
    """Every provider and its state, including the ones not in play.

    resolve_chain drops a provider that has no key, which is right for calling
    but wrong for showing: a missing row makes "Anthropic leads but has no key"
    look identical to "Anthropic is not part of this app". Returns
    [(name, state)] where state is active, standby, no key, or off.
    """
    chain = resolve_chain()
    pinned = os.getenv("AI_PROVIDER", "").strip().lower() in PROVIDER_ORDER

    rows = []
    for name in PROVIDER_ORDER:
        if name == chain[0]:
            state = "active"
        elif name in chain:
            state = "standby"
        else:
            state = "off" if pinned else "no key"
        rows.append((name, state))
    return rows


def complete(system_prompt, user_prompt, raw_text, model=None):
    """Return (raw_json_text, provider_used, failures).

    Falls down the chain on failure. `failures` says why each earlier provider
    did not answer, and is empty on the normal path.

    A bad key, a rate limit or an uninstalled SDK all end with Groq answering in
    Anthropic's place. The result says "groq", which is true but looks identical
    to having configured Groq on purpose, so the reason has to travel with it.
    """
    failures = []

    for provider in resolve_chain():
        try:
            if provider == "anthropic":
                return call_anthropic(system_prompt, user_prompt, model), provider, failures
            if provider == "groq":
                return call_groq(system_prompt, user_prompt, model), provider, failures
            return local_result(raw_text), "local", failures
        except Exception as exc:
            # Record it and try the next one. The last provider is always local,
            # which cannot fail on a network problem, so the chain terminates.
            failures.append(f"{provider}: {describe_failure(exc)}")

    raise ProviderError("Every provider failed.\n" + "\n".join(failures))


def describe_failure(exc):
    """A reason a reader can act on, rather than the repr of an exception.

    A missing SDK is the one worth naming: it looks like an outage in the logs
    but it is a setup problem, and the fix is a pip install, not a retry.
    """
    if isinstance(exc, ImportError):
        return f"the SDK is not installed ({exc})"
    if isinstance(exc, KeyError):
        return f"{exc.args[0]} is not set"
    return f"{type(exc).__name__}: {exc}"


def call_anthropic(system_prompt, user_prompt, model=None):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model or os.getenv("ANTHROPIC_MODEL", ANTHROPIC_DEFAULT_MODEL),
        max_tokens=2000,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )
    if not text:
        raise ProviderError("Anthropic returned no text content.")
    return text


def call_groq(system_prompt, user_prompt, model=None):
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=model or os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL),
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise ProviderError("Groq returned an empty response.")
    return content


# --- the no-key engine --------------------------------------------------------

def classify(line):
    lowered = line.lower()
    for category, needles in KEYWORD_RULES:
        if any(needle in lowered for needle in needles):
            return category
    return "other"


def find_amount(line):
    """Return (amount, currency), ignoring numbers that are really dates."""
    for match in MONEY.finditer(line):
        marker, digits = match.group(1), match.group(2)
        before = line[max(0, match.start() - 1):match.start()]
        after = line[match.end():match.end() + 1]
        # An empty neighbour means start or end of line, which is not a separator.
        # "x in string" is True for the empty string, so test for content first.
        if (before and before in "/-.") or (after and after in "/-."):
            continue  # part of a date like 7/27
        trailing = CURRENCY_AFTER.match(line[match.end():])
        if marker is None and trailing is None and "." not in digits and "," not in digits:
            continue  # a bare integer is more often a quantity than money

        if marker:
            currency = CURRENCY_SIGNS.get(marker, marker.upper())
        elif trailing:
            currency = trailing.group(1).upper()
        else:
            currency = "USD"
        return float(digits.replace(",", "")), currency
    return None, None


def find_date(line):
    """Only a fully written date. A bare 7/27 has no year, so it stays null."""
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", line)
    return match.group(1) if match else None


def local_result(raw_text):
    """Organize a stream with no model at all, in the same JSON shape."""
    result = {
        "project_name": None,
        "client_name": None,
        "property_address": None,
        "items": [],
        "open_actions": [],
        "overall_summary": "",
        "warnings": ["Organized by the local rule-based engine, with no AI model."],
    }

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        header_field = None
        for field, pattern in HEADER_PATTERNS:
            match = pattern.match(line)
            if match:
                result[field] = match.group(1).strip()
                header_field = field
                break
        if header_field:
            continue

        amount, currency = find_amount(line)
        date = find_date(line)
        item_id = f"item_{len(result['items']) + 1:03d}"

        result["items"].append({
            "item_id": item_id,
            "category": classify(line),
            "date": date,
            "amount": amount,
            "currency": currency,
            "title": " ".join(line.split()[:8]),
            "summary": line[:180],
            "action_required": False,
            "confidence": "low",
            "source_excerpt": line,
        })

        if date is None:
            result["warnings"].append(f"{item_id}: no full date was written on this line.")

    count = len(result["items"])
    result["overall_summary"] = (
        f"Organized {count} update{'' if count == 1 else 's'} without a model. "
        f"Every field here was matched by keyword and needs checking."
    )
    return json.dumps(result, ensure_ascii=False)
