# Foreman AI Job Organizer — Option C

A VTSP technical-track prototype that converts a messy stream of construction
job information—notes, texts, receipts, photo captions, deliveries, inspections,
payments, and scheduling updates—into validated structured output.

## What it produces

- Project, client, and address metadata
- Categorized timeline items
- Dates, people, locations, and monetary amounts
- Concise summaries and source excerpts
- Open actions, priorities, confidence labels, and warnings
- Downloadable JSON output

## Privacy

Use only made-up sample data. Never use real Foreman customer, employee, or
company data.

## Fastest setup

### 1. Install Python packages

```bash
python -m pip install -r requirements.txt
```

### 2. Run immediately in demo mode

No API key is needed:

```bash
streamlit run app.py
```

The app automatically enables rule-based demo mode if no Groq key is present.

### 3. Enable real AI extraction with Groq

1. Create a free Groq API key.
2. Copy `.env.example` to `.env`.
3. Put the key in `.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

4. Restart Streamlit and disable **Demo mode** in the sidebar.

The model name is configurable because providers can retire or replace models.

## Run the batch processor

Process every `.txt` file in `data/samples` and save JSON outputs plus a CSV
results log:

```bash
python -m src.batch
```

Force no-key demo mode:

```bash
python -m src.batch --demo
```

## Run tests

```bash
pytest
```

## Repository structure

```text
foreman_job_organizer/
├── app.py
├── data/
│   └── samples/
├── outputs/
├── src/
│   ├── batch.py
│   ├── demo_mode.py
│   ├── organizer.py
│   ├── prompts.py
│   └── schema.py
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Core pipeline

1. Take raw text.
2. Build an explicit extraction prompt with a strict JSON schema.
3. Call Groq, or use rule-based demo mode.
4. Extract and parse the JSON safely.
5. Validate required fields and allowed values with Pydantic.
6. Return a structured result or flag the error.
7. Save results individually or process a folder in one robust batch run.

## Missing-data rule

When information is absent or genuinely ambiguous, the AI must return `null`
and add an explanatory warning. It must not guess. Ambiguous or risky items
should be flagged for human review.

