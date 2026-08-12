# Screenshots for the deck

Drop them in this folder with these names, so `SLIDE_PACK.md` and the deck can
point at something stable:

| File | What it shows |
|---|---|
| `01-app-landing.png` | The app on open — sidebar, sample picker, input box |
| `02-timeline.png` | A finished run on `03_tricky_bathroom` — the timeline |
| `03-warnings.png` | The warnings and open actions under the timeline |

`02-timeline.png` is the one that carries a slide on its own. If you only take
one, take that.

## Taking them

The app has to be running and a sample has to be organized, so these come from a
live run rather than anything scripted:

```bash
streamlit run app.py
```

Then:

1. Screenshot the page as it opens → `01-app-landing.png`
2. Sidebar → pick `03_tricky_bathroom` → **Organize**, wait for it to finish
3. Screenshot the timeline → `02-timeline.png`
4. Scroll to the warnings and open actions → `03-warnings.png`

On Windows, `Win + Shift + S` crops a region straight to the clipboard.

Two things to check before you keep a shot:

- The provider badge should not say **local**. The local engine is the no-key
  fallback and it is much worse — a screenshot of it is not representative, and
  the app prints a red warning that will be in the picture.
- The sample must be one of ours from `data/samples/`. Never screenshot real
  Foreman data.
