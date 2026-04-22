# GUI Plan — MyPySkinDose

> See also: [CODEBASE_OVERVIEW.md](CODEBASE_OVERVIEW.md) | [UI_ANALYSIS.md](UI_ANALYSIS.md) | [AGENTS.md](../AGENTS.md)

_Last updated: 2026-04-22_

---

## 1. Goal

Build a standalone, browser-based GUI that lets **non-Python users** (medical physicists, radiologists, radiation safety officers) upload a DICOM RDSR file, configure a patient phantom, run a skin dose calculation, and view/export results — all without touching the command line or editing JSON.

---

## 2. Framework decision: Gradio vs Streamlit vs others

### 2.1 Candidate comparison

| Criterion | Gradio | Streamlit | Panel | ipywidgets (notebook) |
|-----------|--------|-----------|-------|-----------------------|
| Setup complexity | Very low | Low | Medium | Very low (notebook only) |
| File upload widget | ✅ built-in | ✅ built-in | ✅ | ✅ (limited) |
| Plotly support | ✅ native | ✅ native | ✅ native | ✅ |
| Multi-step workflow | ⚠️ tabs only | ✅ pages/sidebar | ✅ | ⚠️ |
| Progress bar | ✅ `gr.Progress` | ✅ `st.progress` | ✅ | ✅ tqdm |
| Lay-person friendliness | ✅ very high | ✅ high | Medium | Low (requires Jupyter) |
| Shareable / deployable | ✅ HuggingFace Spaces | ✅ Streamlit Cloud | ✅ | ❌ |
| Effort for prototype | ~1 day | ~2 days | ~3 days | ~0.5 days |
| Effort for full app | ~3 days | ~4–5 days | ~5–7 days | N/A |
| Learning curve for maintainers | Very low | Low | Medium | Low |

### 2.2 Recommendation: **Streamlit**

Gradio is excellent for single-function demos (upload → run → result). But our workflow is inherently **multi-step**:

1. Upload RDSR
2. Preview geometry (optional but valuable)
3. Configure phantom and settings
4. Run dose calculation (long-running, needs progress)
5. View interactive dose map
6. Export results

Streamlit handles this naturally with:
- A **sidebar** for all settings (always visible)
- **Multiple pages** or tabs for the workflow steps
- `st.session_state` to carry data between steps without re-running
- `st.plotly_chart` renders our existing Plotly figures with zero changes
- `st.progress` + `st.status` for the calculation step
- `st.download_button` for export

Gradio's `gr.Blocks` with tabs can also do this, but Streamlit's layout model is more natural for a multi-step clinical workflow and its output looks more like a real application to end users.

**Both are easy to install and use for lay-people** — the user just runs one command and a browser tab opens. Neither requires any frontend knowledge to maintain.

### 2.3 Should we add it to requirements.txt?

Yes — add `streamlit` as an **optional** dependency in `pyproject.toml` under a `[gui]` extra, and add it to `requirements.txt` for development. This way:
- Core library users don't get Streamlit installed automatically
- GUI users install with `pip install mypyskindose[gui]`
- Developers get it via `requirements.txt`

### 2.4 Local-only deployment

The app is intended to run **locally on the user's machine** — not hosted in the cloud. This is the right call for a medical tool handling DICOM files that may contain patient identifiers (PHI). Streamlit's local server model (`localhost:8501`) is a perfect fit:
- No data ever leaves the machine
- No authentication or rate-limiting needed
- Works offline
- The "run a command, browser opens" UX is already familiar to anyone who has used Jupyter

Users can also pass local file paths directly in addition to using the file uploader widget.

```toml
# pyproject.toml addition
[project.optional-dependencies]
gui = ["streamlit>=1.35.0"]
```

```
# requirements.txt addition
streamlit>=1.35.0
```

---

## 3. Proposed app structure

```
src/mypyskindose/gui/
  __init__.py
  app.py                  # Streamlit entry point — run with: streamlit run app.py
  pages/
    1_upload.py           # Step 1: Upload RDSR + quick metadata preview
    2_geometry.py         # Step 2: Geometry preview (plot_setup / plot_procedure)
    3_settings.py         # Step 3: Phantom + calculation settings
    4_calculate.py        # Step 4: Run dose calculation with progress
    5_results.py          # Step 5: Dose map + PSD + correction factors
    6_export.py           # Step 6: Export (JSON, HTML report, PNG)
  components/
    settings_sidebar.py   # Reusable sidebar widget (phantom, offsets, k_tab, etc.)
    plotly_viewer.py      # Wrapper to render mypyskindose Plotly figures in st
    results_table.py      # Correction factor breakdown table
    report_builder.py     # HTML/PDF report generation
  state.py                # Session state keys and helpers
```

### Entry point

```bash
streamlit run src/mypyskindose/gui/app.py
```

Or via CLI:

```bash
python -m mypyskindose --gui
```

(Wire `--gui` in `main.py` to call `subprocess.run(["streamlit", "run", ...])`)

---

## 4. Screen-by-screen design

### Page 1 — Upload RDSR

**Purpose:** Get the RDSR file into the app and show the user what's in it.

**Widgets:**
- `st.file_uploader("Upload DICOM RDSR file", type=["dcm"])` — drag-and-drop
- OR `st.text_input("Or enter file path")` — for power users
- "Use example file" dropdown — loads one of the bundled `.dcm` files from `example_data/RDSR/`

**On upload:**
- Parse RDSR with `rdsr_parser` + `rdsr_normalizer`
- Show a summary table: number of events, date, device model, total air kerma
- Show a per-event table (collapsible): event index, kVp, mAs, beam angles, field size

**State saved:** parsed DataFrame, file path

---

### Page 2 — Geometry Preview (optional)

**Purpose:** Let the user visually verify the phantom placement and beam geometry before running the full calculation.

**Widgets:**
- "Phantom model" dropdown: `plane`, `cylinder`, `human`
- "Human mesh" dropdown (if human): `hudfrid`, `adult_male`, `adult_female`, `junior_male`, `junior_female`
- "Patient orientation" radio: `head_first_supine`, `feet_first_supine`
- Patient offset sliders: d_lon, d_ver, d_lat (range ±30 cm)
- "Preview setup" button → runs `mode="plot_setup"`, shows Plotly figure
- Event index slider (0 to N-1) + "Preview event" button → runs `mode="plot_event"`
- "Preview full procedure" button → runs `mode="plot_procedure"` (slider through all events)

**Note:** These are fast operations (no dose calculation), so they can run on button click without a progress bar.

---

### Page 3 — Settings

**Purpose:** Configure all calculation parameters in a form, with sensible defaults and tooltips.

**Sections (use `st.expander` for each):**

**Phantom settings:**
- Model (dropdown)
- Human mesh (dropdown, conditional)
- Patient orientation (radio)
- Patient offset (3 number inputs: d_lon, d_ver, d_lat)

**Physics settings:**
- Table transmission k_tab (slider 0.0–1.0, default 0.8)
- "Use estimated k_tab" checkbox (if unchecked, use measured from DB)
- Inherent filtration in mmAl (number input, default 3.1)
- Remove invalid RDSR rows (checkbox)

**Output settings:**
- Plot dose map after calculation (checkbox)
- Dark mode (checkbox)

**Validation:** Show `st.warning` or `st.error` inline if values are out of range.

---

### Page 4 — Calculate

**Purpose:** Run the dose calculation with visible progress feedback.

**Widgets:**
- Summary of current settings (read-only, from session state)
- "Run calculation" button
- `st.progress` bar + `st.status` text showing current event number
- Estimated time remaining (based on events processed so far)

**On completion:**
- Show PSD result prominently: `st.metric("Peak Skin Dose", f"{psd:.1f} mGy")`
- Show total air kerma
- Auto-navigate to Results page

**Error handling:**
- Catch exceptions, show `st.error` with the message
- Show a "Download error log" button for debugging

---

### Page 5 — Results

**Purpose:** Display the dose map and correction factor breakdown.

**Widgets:**
- `st.metric` cards: PSD (mGy), air kerma (mGy), number of events, max correction factor
- Interactive 3D dose map (Plotly figure via `st.plotly_chart`)
- Correction factor table: per-event k_isq, k_bs, k_med, k_tab (sortable)
- "Show dose map colorscale" selector (jet, viridis, plasma, etc.)
- "Camera view" buttons: AP, LAT, PA (update Plotly camera)

---

### Page 6 — Export

**Purpose:** Let the user save results in useful formats.

**Options:**
- `st.download_button("Download JSON results")` — full output dict as JSON
- `st.download_button("Download dose map HTML")` — interactive Plotly HTML
- `st.download_button("Download dose map PNG")` — static image via kaleido
- `st.download_button("Download PDF report")` — structured report (Phase 2)

**PDF report contents (Phase 2):**
- Procedure metadata (device, date, number of events)
- Settings used
- PSD and air kerma values
- Dose map image
- Correction factor summary table

---

## 5. Sidebar (persistent across all pages)

The sidebar shows the current state at a glance:

```
📁 File: philips_allura_clarity_u104.dcm
📊 Events: 47
👤 Phantom: human / hudfrid
🔧 k_tab: 0.80
📐 Orientation: head_first_supine

[Run Calculation]  ← shortcut button
```

---

## 6. Session state design

All inter-page data lives in `st.session_state`. Key entries:

| Key | Type | Description |
|-----|------|-------------|
| `rdsr_df` | `pd.DataFrame` | Normalised RDSR data |
| `file_path` | `str` | Path to uploaded/temp RDSR file |
| `settings` | `PyskindoseSettings` | Current settings object |
| `output` | `dict` | Result from `main()` |
| `plotly_fig` | `go.Figure` | Current dose map figure |
| `calculation_done` | `bool` | Whether results are available |

Helper functions in `state.py`:
- `get_settings()` → builds `PyskindoseSettings` from session state
- `reset_results()` → clears output when settings change
- `is_ready_to_calculate()` → checks file + settings are set

---

## 7. Wiring into the existing CLI

In `main.py`, add:

```python
elif args.mode == "gui":
    import subprocess, sys
    gui_app = Path(__file__).parent / "gui" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(gui_app)])
```

So users can do:

```bash
python -m mypyskindose --gui
```

---

## 8. Implementation phases

### Phase 1 — Minimal working app (~2–3 days)

Goal: upload RDSR → configure phantom → run calculation → see PSD + dose map.

Files to create:
- `src/mypyskindose/gui/__init__.py`
- `src/mypyskindose/gui/app.py` — single-page Streamlit app with sidebar
- `src/mypyskindose/gui/state.py` — session state helpers

Functionality:
- File upload (RDSR or example file selector)
- Phantom model + mesh selector
- k_tab slider
- Run button with progress
- PSD metric display
- Dose map Plotly figure

### Phase 2 — Full multi-page app (~3–4 more days)

- Split into pages (upload, geometry preview, settings, calculate, results, export)
- Geometry preview (plot_setup, plot_event, plot_procedure)
- Full settings form with validation
- Correction factor table
- JSON + HTML export

### Phase 3 — Report generation (~2–3 more days)

- PDF report via `weasyprint` or `reportlab`
- Report template with dose map image, metadata, correction table
- Add `report` optional dependency

### Phase 4 — Polish (~1–2 days)

- Custom CSS for clinical look (white background, clear typography)
- Help tooltips on every setting (explain what k_tab, HVL, etc. mean)
- "What is this?" expandable explanations for non-physicists
- Error messages that are human-readable (not Python tracebacks)

---

## 9. Gradio as an alternative

Not recommended for this use case. Gradio's main advantage is easy public deployment (HuggingFace Spaces), which isn't needed here. For a local multi-step clinical workflow, Streamlit's layout model is cleaner. Gradio `gr.Blocks` with tabs can technically replicate the flow, but requires more boilerplate for state management between steps.

---

## 10. Open questions before starting

1. ~~**Deployment target:**~~ **Resolved — local only.** All processing is on the user's machine. No PHI leaves the device. Streamlit's `localhost` model is ideal for this.

2. **Calculation time:** How long does a typical RDSR take? If >30 seconds, we need async/threading so the UI doesn't freeze.
   - Use `st.spinner` + run calculation in a thread via `concurrent.futures`

3. **Windows compatibility:** The target users are likely on Windows. Streamlit works well on Windows. For PDF export, prefer `reportlab` over `weasyprint` (weasyprint has Windows quirks).

4. **Single-file vs package:** For Phase 1, a single `app.py` is easiest to distribute and run. Refactor into pages/components in Phase 2.

---

## 11. Immediate next steps

1. Add `streamlit>=1.35.0` to `requirements.txt` and as `[gui]` optional dep in `pyproject.toml`
2. Install: `pip install streamlit`
3. Create `src/mypyskindose/gui/__init__.py` (empty)
4. Create `src/mypyskindose/gui/app.py` — Phase 1 single-page app
5. Test with one of the bundled example RDSR files
6. Wire `--gui` in `main.py`
