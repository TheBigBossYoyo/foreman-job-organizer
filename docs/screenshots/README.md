# Screenshots for the deck

Taken 12 August 2026 from a live run on `main`. Groq answered, not
the local fallback — the sidebar in every shot shows which provider was active,
so the picture states its own provenance.

| File | What it shows |
|---|---|
| `01-app-landing.png` | The app on open — sidebar, provider status, sample loaded, input box |
| `02-timeline.png` | A finished run on `03_tricky_bathroom` — the full timeline |
| `03-warnings.png` | Open actions as checkboxes, the warnings expanded, and the three downloads |
| `04-job-record.png` | The printable job record, rendered from `06_safety_incident` |

`02-timeline.png` carries a slide on its own. If you use only one, use that.

What to point at in `02`:

- **Every item says NO DATE**, and the counter reads *5 of 5 items undated in the
  source*. The input's only date is `7/27` with no year. Nothing was invented.
- **LOW CONFIDENCE** on the Lopez site visit. The model is unsure and says so
  instead of filing it as a booking.
- **The grey line under each item** is the source excerpt. Every row traces back
  to the input line it came from.

`04-job-record.png` is the printable record, not the app. It is the one output
meant to leave the building, so it carries the generated date, the engine that
produced it, and the warnings in full.

## Retaking them

The app has to be running, and the timeline shots need a real run:

```bash
streamlit run app.py
```

Then pick `03_tricky_bathroom.txt` in the sidebar, press **Organize**, and
capture. `Win + Shift + S` crops a region to the clipboard on Windows.

Two things to check before keeping a shot:

- The provider must not be **Local engine**. That is the no-key fallback and it
  is much worse — the app prints a red warning that will be in the picture.
- The sample must be one of ours from `data/samples/`. Never screenshot real
  Foreman data.
