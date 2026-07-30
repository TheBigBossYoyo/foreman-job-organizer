from __future__ import annotations

SYSTEM_PROMPT = """
You are an AI job organizer for a construction contractor.

Your task is to convert a messy stream of notes, messages, receipts, photo
captions, deliveries, inspections, payments, and scheduling updates into
structured JSON.

Rules:
1. Use only facts found in the input. Never invent facts, prices, dates,
   names, addresses, or actions.
2. When a value is missing or genuinely ambiguous, use null.
3. Dates must use YYYY-MM-DD. If only a month/day is shown and the year cannot
   be safely inferred, use null and add a warning.
4. Currency must be a three-letter code, such as USD, EUR, GBP, or TND.
5. Split the input into separate items when it contains distinct events.
6. "source_excerpt" must quote a short supporting fragment from the input.
7. If an issue, deadline, missing item, approval, repair, payment, inspection,
   or follow-up requires attention, set action_required to true and write a
   concise action.
8. Return ONLY one valid JSON object. Do not use markdown fences or commentary.

The output must follow this exact shape:
{
  "project_name": null,
  "client_name": null,
  "property_address": null,
  "items": [
    {
      "item_id": "item_001",
      "category": "photo | receipt | client_update | contractor_update | inspection | delivery | schedule | issue | payment | other",
      "date": "YYYY-MM-DD or null",
      "people": [],
      "location": null,
      "amount": null,
      "currency": null,
      "title": "",
      "summary": "",
      "action_required": false,
      "action": null,
      "priority": "low | medium | high | urgent",
      "confidence": "low | medium | high",
      "source_excerpt": ""
    }
  ],
  "open_actions": [],
  "overall_summary": "",
  "warnings": []
}
""".strip()


WORKED_EXAMPLE_INPUT = """
Project: Rivera kitchen remodel
Address: 12 Oak Street
2026-07-20 - Sam: Cabinets arrived, but two upper doors are scratched.
Receipt: Home Supply, cabinet hardware, $184.50.
Client text: "Can we move Friday's inspection to Monday?"
""".strip()


WORKED_EXAMPLE_OUTPUT = """
{
  "project_name": "Rivera kitchen remodel",
  "client_name": "Rivera",
  "property_address": "12 Oak Street",
  "items": [
    {
      "item_id": "item_001",
      "category": "delivery",
      "date": "2026-07-20",
      "people": ["Sam"],
      "location": null,
      "amount": null,
      "currency": null,
      "title": "Cabinet delivery",
      "summary": "Cabinets arrived and two upper doors were scratched.",
      "action_required": true,
      "action": "Document the damage and arrange replacement doors.",
      "priority": "high",
      "confidence": "high",
      "source_excerpt": "Cabinets arrived, but two upper doors are scratched."
    },
    {
      "item_id": "item_002",
      "category": "receipt",
      "date": null,
      "people": [],
      "location": "Home Supply",
      "amount": 184.5,
      "currency": "USD",
      "title": "Cabinet hardware receipt",
      "summary": "Receipt for cabinet hardware from Home Supply.",
      "action_required": false,
      "action": null,
      "priority": "low",
      "confidence": "high",
      "source_excerpt": "Home Supply, cabinet hardware, $184.50."
    },
    {
      "item_id": "item_003",
      "category": "schedule",
      "date": null,
      "people": ["Rivera"],
      "location": null,
      "amount": null,
      "currency": null,
      "title": "Inspection reschedule request",
      "summary": "The client asked to move Friday's inspection to Monday.",
      "action_required": true,
      "action": "Confirm whether the inspection can be moved to Monday.",
      "priority": "medium",
      "confidence": "medium",
      "source_excerpt": "Can we move Friday's inspection to Monday?"
    }
  ],
  "open_actions": [
    "Document the scratched cabinet doors and arrange replacements.",
    "Confirm whether the inspection can be moved to Monday."
  ],
  "overall_summary": "Cabinets arrived with damage, a hardware receipt was recorded, and the client requested an inspection reschedule.",
  "warnings": [
    "The receipt date was not provided.",
    "Exact calendar dates for Friday and Monday were not provided."
  ]
}
""".strip()


def build_user_prompt(raw_text: str) -> str:
    return f"""
Worked example input:
{WORKED_EXAMPLE_INPUT}

Worked example output:
{WORKED_EXAMPLE_OUTPUT}

Now organize the following job stream.

INPUT:
{raw_text}

Return ONLY valid JSON.
""".strip()
