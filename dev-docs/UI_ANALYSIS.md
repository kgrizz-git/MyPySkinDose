# UI Analysis — What Exists and How to Improve It

> See also: [CODEBASE_OVERVIEW.md](CODEBASE_OVERVIEW.md) | [GUI_PLAN.md](GUI_PLAN.md) | [AGENTS.md](../AGENTS.md)

**→ The detailed implementation plan is in [GUI_PLAN.md](GUI_PLAN.md).**

---

## What UI exists today

### 1. Interactive Plotly plots (in-browser / in-notebook)

The only "UI" today is a set of interactive [Plotly](https://plotly.com/python/) 3D plots rendered either in a Jupyter notebook cell or as a standalone HTML file opened in a browser.

**What they show:**

| Mode | Plot content |
|------|-------------|
| `plot_setup` | Phantom + table + pad + beam in zero-angle starting position |
| `plot_event` | Full 3D geometry for one specific irradiation event |
| `plot_procedure` | All events with a **slider** to step through them one by one |
| `calculate_dose` | 3D dose map coloured by accumulated skin dose on the phantom |

**Interactivity available:**
- Rotate, zoom, pan the 3D scene with mouse
- Hover over phantom cells to see dose values
- Slider in `plot_procedure` to step through events
- Dark/light mode toggle (via `settings.plot.dark_mode`)
- Colorscale selection for dose map (e.g. `"jet"`)

**How plots are triggered:**
- `main()` → `analyze_data()` → `create_geometry_plot()` or `create_dose_map_plot()`
- Plots are either shown inline (notebook) or saved to `PlotOutputs/` as `.html` / `.png`

### 2. Jupyter Notebook (`getting_started.ipynb`)

Located at `docs/source/getting_started/getting_started.ipynb`. This is the closest thing to a guided UI — a step-by-step walkthrough that lets users:
- Load and inspect settings
- Choose phantom model and positioning
- Load an RDSR file
- Run geometry inspection and dose calculation
- View results inline

It is the recommended starting point for new users.

### 3. CLI (`main.py`)

A minimal `argparse`-based CLI:

```bash
python -m mypyskindose.main --file-path path/to/file.dcm --settings path/to/settings.json --mode headless
```

Supports `--mode headless` and `--mode gui` (launches the NiceGUI web application).

### 4. NiceGUI Web Application (Implemented)

A full-featured web application built with [NiceGUI](https://nicegui.io/) located in `src/mypyskindose/gui/app.py`.

**Current Version:** 1.1.0

**Aesthetic:** Sleek Modern/Material design with glassmorphism effects

**Features:**
- 7-tab interface: Upload, Data Table, Settings, Geometry, Calculate, Results, Export
- RDSR file upload with drag-and-drop support
- Example RDSR file loader
- Interactive data table with normalized/raw view toggle
- Comprehensive settings form (phantom, physics, visual settings)
- Geometry preview with setup/event/procedure views
- Dose calculation with progress feedback
- Results display with PSD, air kerma, and event count metrics
- Interactive 3D dose map with colorscale selection
- Correction factors table per event
- Export options: JSON, HTML, PNG

**Design Characteristics:**
- 12px rounded corners on all cards and buttons
- Glassmorphism with 20px backdrop blur and 45% card opacity
- Gradient buttons (teal for primary, purple for secondary)
- Scale-based hover effects (1.02x enlargement)
- Navigation with vertical line active indicator
- Aurora background gradients with enhanced depth
- Inner glow shadows instead of hard borders

**Launch:**
```bash
python -m mypyskindose --mode gui
# or
python src/mypyskindose/main.py --mode gui
```

The GUI runs on http://localhost:8765 by default.

### 5. Rich terminal output

`settings.print_parameters()` uses the [Rich](https://github.com/Textualize/rich) library to print a colour-formatted summary of all settings to the terminal. This is the only non-Plotly UI element.

---

## What is missing / pain points

### For end users (clinicians, physicists)
- ~~No standalone desktop or web application — must know Python~~ (NiceGUI app implemented)
- ~~No file picker — RDSR file path must be typed as a string~~ (Drag-and-drop upload implemented)
- ~~No form-based settings editor — settings require editing JSON or Python code~~ (Settings form implemented)
- No way to compare two procedures or two phantom configurations side by side
- No summary report export (PDF, Word) — only raw dict/JSON/HTML/PNG
- ~~No progress feedback beyond a tqdm bar in the terminal~~ (Progress bar in GUI implemented)

### For developers
- Settings are scattered across a JSON file + multiple Python classes — hard to discover
- No validation feedback when settings are wrong (errors surface deep in the stack)
- No hot-reload: changing settings requires re-running the full pipeline
- Normalization settings for new vendors require editing a JSON file manually

---

## Options for a GUI

### Option A — Gradio web app (recommended for fastest path)

[Gradio](https://www.gradio.app/) wraps Python functions in a web UI with minimal code. It runs locally and opens in a browser.

**Why it fits:**
- Zero frontend knowledge needed
- File upload widget handles RDSR file selection
- Sliders, dropdowns, and number inputs map directly to settings fields
- Plotly figures render natively in Gradio
- Can be deployed to Hugging Face Spaces for sharing

**Rough structure:**

```python
import gradio as gr
from mypyskindose import PyskindoseSettings, load_settings_example_json
from mypyskindose.main import main

def run_dose_calculation(rdsr_file, phantom_model, human_mesh, k_tab_val, ...):
    settings = PyskindoseSettings(settings=load_settings_example_json())
    settings.mode = "calculate_dose"
    settings.phantom.model = phantom_model
    settings.phantom.human_mesh = human_mesh
    settings.k_tab_val = k_tab_val
    output = main(file_path=rdsr_file.name, settings=settings)
    return output["psd"], plotly_figure

demo = gr.Interface(
    fn=run_dose_calculation,
    inputs=[
        gr.File(label="RDSR DICOM file"),
        gr.Dropdown(["plane", "cylinder", "human"], label="Phantom model"),
        gr.Dropdown(["hudfrid", "adult_male", "adult_female"], label="Human mesh"),
        gr.Slider(0.0, 1.0, value=0.8, label="Table transmission (k_tab)"),
    ],
    outputs=[
        gr.Number(label="Peak Skin Dose (mGy)"),
        gr.Plot(label="Dose map"),
    ],
)
demo.launch()
```

**Effort:** ~1–2 days for a functional prototype.

---

### Option B — Streamlit web app

[Streamlit](https://streamlit.io/) is similar to Gradio but gives more layout control and is better for multi-step workflows.

**Why it fits:**
- Sidebar for settings, main area for plots
- `st.file_uploader` for RDSR files
- `st.plotly_chart` renders Plotly figures natively
- Session state allows multi-step workflow (setup → inspect → calculate)
- Easy to add a results summary section

**Rough structure:**

```
Page 1: Upload RDSR + configure settings
Page 2: Inspect geometry (plot_setup / plot_procedure)
Page 3: Run dose calculation + view dose map
Page 4: Export results (JSON / HTML report)
```

**Effort:** ~2–4 days for a functional multi-page app.

---

### Option C — Panel / Holoviz dashboard

[Panel](https://panel.holoviz.org/) integrates tightly with Plotly and supports reactive widgets. Good if you want a more "dashboard" feel with live-updating plots as settings change.

**Effort:** ~3–5 days.

---

### Option D — Extend the Jupyter notebook

The existing `getting_started.ipynb` could be extended with [ipywidgets](https://ipywidgets.readthedocs.io/) to add interactive controls (file picker, sliders, dropdowns) without leaving the notebook environment.

**Why it fits:**
- No new dependencies beyond `ipywidgets`
- Familiar environment for medical physicists
- Can be served via JupyterHub for multi-user access

**Effort:** ~1 day to add widgets to the existing notebook.

---

## Recommended roadmap

### Phase 1 — Quick wins (no new framework)

1. **Add `ipywidgets` to the getting-started notebook** — file picker, phantom selector, k_tab slider, orientation dropdown. This gives a usable interactive UI in ~1 day.
2. **Add settings validation** in `PyskindoseSettings.__init__` with clear error messages for invalid values.
3. **Add a `--gui` flag** to the CLI that launches a Gradio or Streamlit app.

### Phase 2 — Standalone web app (Gradio or Streamlit)

Build a `src/mypyskindose/gui/` module with:

```
gui/
  app.py              # Gradio or Streamlit entry point
  settings_form.py    # Settings widgets
  results_view.py     # Dose map + PSD display
  report_export.py    # PDF/HTML report generation
```

Key screens:
1. **Setup** — upload RDSR, choose phantom, set patient offset and orientation
2. **Geometry preview** — `plot_setup` / `plot_procedure` inline
3. **Dose calculation** — run with progress bar, show PSD result
4. **Results** — interactive dose map, correction factor breakdown, export button

### Phase 3 — Report generation

Add a report template (HTML → PDF via `weasyprint` or `reportlab`) that includes:
- Patient/procedure metadata from RDSR
- Dose map image
- PSD value and air kerma
- Correction factor summary table
- Settings used

---

## Files to create/modify for a GUI

| File | Action | Notes |
|------|--------|-------|
| `src/mypyskindose/gui/__init__.py` | Create | New GUI module |
| `src/mypyskindose/gui/app.py` | Create | Main Gradio/Streamlit app |
| `src/mypyskindose/main.py` | Modify | Wire `--mode gui` to launch `app.py` |
| `pyproject.toml` | Modify | Add `gradio` or `streamlit` as optional dependency |
| `docs/source/getting_started/getting_started.ipynb` | Modify | Add ipywidgets controls |

---

## Notes on the existing Plotly plots

The existing plots are already quite good — interactive, 3D, with hover tooltips. The main gap is that they are only accessible by running Python code. Wrapping them in a Gradio/Streamlit app would expose them to non-Python users with no changes to the plotting code itself.

The `PlotOutputs/` directory already receives saved HTML files — a GUI could simply open these in an iframe or link to them.
