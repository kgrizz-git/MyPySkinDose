"""MyPySkinDose — NiceGUI app (Phase 1).

Run with:
    python src/mypyskindose/main.py --mode gui
or directly:
    .venv/Scripts/python -m mypyskindose --mode gui
    .venv/Scripts/python -m mypyskindose --mode gui --native
"""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
from pathlib import Path

from nicegui import app, run, ui

from .helpers import (
    build_settings,
    get_example_rdsr_files,
    get_human_mesh_names,
    load_rdsr,
    run_calculation,
)
from .state import reset_results, state
from mypyskindose.debug import dprint

# ── constants ──────────────────────────────────────────────────────────────
HUMAN_MESHES = get_human_mesh_names()
EXAMPLE_FILES = {p.name: p for p in get_example_rdsr_files()}
COLORSCALES = ["jet", "viridis", "plasma", "inferno", "magma", "turbo", "hot"]
PHANTOM_MODELS = ["human", "cylinder", "plane"]
ORIENTATIONS = ["head_first_supine", "feet_first_supine"]


# ── page ───────────────────────────────────────────────────────────────────
@ui.page("/")
def index():
    dprint("GUI", "Rendering index page (client connected or reloaded)")
    dark = ui.dark_mode(state.dark_mode)

    # ── header ────────────────────────────────────────────────────────────
    with ui.header(elevated=True).classes("items-center justify-between px-4"):
        ui.label("MyPySkinDose").classes("text-h6 font-bold")
        with ui.row().classes("items-center gap-2"):
            ui.label("Dark mode")
            ui.switch(value=state.dark_mode).bind_value(state, "dark_mode").on(
                "update:model-value", lambda: dark.set_value(state.dark_mode)
            )

    # ── left drawer ───────────────────────────────────────────────────────
    with ui.left_drawer(fixed=True).classes("bg-grey-9 q-pa-md").style("width:220px"):
        ui.label("Status").classes("text-subtitle2 text-grey-4 q-mb-xs")

        file_label = ui.label("No file loaded").classes("text-caption text-grey-5")
        events_label = ui.label("").classes("text-caption text-grey-5")
        psd_label = ui.label("").classes("text-caption text-positive text-bold")

        ui.separator().classes("q-my-sm")
        ui.label("Navigation").classes("text-subtitle2 text-grey-4 q-mb-xs")

        def go(name: str):
            tabs.set_value(name)
            state.active_tab = name

        ui.button("1 · Upload", on_click=lambda: go("upload")).props("flat align=left").classes("full-width text-left")
        ui.button("2 · Geometry", on_click=lambda: go("geometry")).props("flat align=left").classes("full-width")
        ui.button("3 · Settings", on_click=lambda: go("settings")).props("flat align=left").classes("full-width")
        ui.button("4 · Calculate", on_click=lambda: go("calculate")).props("flat align=left").classes("full-width")
        ui.button("5 · Results", on_click=lambda: go("results")).props("flat align=left").classes("full-width")
        ui.button("6 · Export", on_click=lambda: go("export")).props("flat align=left").classes("full-width")

        ui.separator().classes("q-my-sm")
        run_btn_drawer = ui.button("▶  Run Calculation", color="positive").classes("full-width")

    # ── main tabs ─────────────────────────────────────────────────────────
    with ui.tabs().classes("w-full").on("update:model-value", lambda e: setattr(state, "active_tab", e.args)) as tabs:
        t_upload = ui.tab("upload", label="1 · Upload")
        t_geometry = ui.tab("geometry", label="2 · Geometry")
        t_settings = ui.tab("settings", label="3 · Settings")
        t_calculate = ui.tab("calculate", label="4 · Calculate")
        t_results = ui.tab("results", label="5 · Results")
        t_export = ui.tab("export", label="6 · Export")

    with ui.tab_panels(tabs, value="upload").classes("w-full"):

        # ══════════════════════════════════════════════════════════════════
        # TAB 1 — UPLOAD
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("upload"):
            ui.label("Load RDSR File").classes("text-h6 q-mb-md")

            with ui.card().classes("w-full q-mb-md"):
                ui.label("Upload a DICOM RDSR (.dcm) file").classes("text-subtitle2 q-mb-sm")

                upload_status = ui.label("").classes("text-caption")

                async def handle_upload(e):
                    dprint("GUI", f"Uploading file {e.name}")
                    with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as tmp:
                        tmp.write(e.content.read())
                        tmp_path = Path(tmp.name)
                    upload_status.set_text("Parsing…")
                    ok, msg = await run.io_bound(load_rdsr, tmp_path, state)
                    if ok:
                        state.file_name = e.name
                        file_label.set_text(f"📁 {e.name}")
                        events_label.set_text(f"📊 {len(state.rdsr_df)} events")
                        upload_status.set_text(msg)
                        ui.notify(msg, type="positive")
                        reset_results()
                        _refresh_event_table()
                    else:
                        upload_status.set_text("Error — see notification")
                        ui.notify(f"Parse error: {msg[:200]}", type="negative", timeout=8000)

                ui.upload(on_upload=handle_upload, label="Drop .dcm here or click").props(
                    'accept=".dcm" flat bordered'
                ).classes("w-full")

            with ui.card().classes("w-full q-mb-md"):
                ui.label("Or use a bundled example file").classes("text-subtitle2 q-mb-sm")

                example_select = ui.select(
                    options=list(EXAMPLE_FILES.keys()),
                    label="Example RDSR file",
                    value=list(EXAMPLE_FILES.keys())[0] if EXAMPLE_FILES else None,
                ).classes("w-full")

                async def load_example():
                    name = example_select.value
                    if not name:
                        return
                    path = EXAMPLE_FILES[name]
                    upload_status.set_text("Parsing…")
                    ok, msg = await run.io_bound(load_rdsr, path, state)
                    if ok:
                        file_label.set_text(f"📁 {name}")
                        events_label.set_text(f"📊 {len(state.rdsr_df)} events")
                        upload_status.set_text(msg)
                        ui.notify(msg, type="positive")
                        reset_results()
                        _refresh_event_table()
                    else:
                        ui.notify(f"Parse error: {msg[:200]}", type="negative", timeout=8000)

                ui.button("Load example", on_click=load_example).props("outline")

            # event summary table
            ui.label("Irradiation events").classes("text-subtitle2 q-mt-md q-mb-xs")
            event_table = ui.table(
                columns=[
                    {"name": "idx", "label": "#", "field": "idx", "align": "right"},
                    {"name": "kVp", "label": "kVp", "field": "kVp", "align": "right"},
                    {"name": "Ap1", "label": "Ap1 (°)", "field": "Ap1", "align": "right"},
                    {"name": "Ap2", "label": "Ap2 (°)", "field": "Ap2", "align": "right"},
                    {"name": "K_IRP", "label": "K_IRP (mGy)", "field": "K_IRP", "align": "right"},
                ],
                rows=[],
                row_key="idx",
            ).classes("w-full")

            def _refresh_event_table():
                if state.rdsr_df is None:
                    return
                df = state.rdsr_df
                rows = []
                for i, row in df.iterrows():
                    rows.append({
                        "idx": i + 1,
                        "kVp": round(float(row.get("kVp", 0)), 1),
                        "Ap1": round(float(row.get("Ap1", 0)), 1),
                        "Ap2": round(float(row.get("Ap2", 0)), 1),
                        "K_IRP": round(float(row.get("K_IRP", 0)), 3),
                    })
                event_table.rows = rows
                event_table.update()

        # ══════════════════════════════════════════════════════════════════
        # TAB 2 — GEOMETRY PREVIEW
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("geometry"):
            ui.label("Geometry Preview").classes("text-h6 q-mb-md")
            ui.label(
                "Visualise phantom placement and beam geometry before running the full calculation."
            ).classes("text-caption text-grey-6 q-mb-md")

            with ui.row().classes("gap-4 q-mb-md"):
                geom_event_input = ui.number(
                    label="Event index (0-based)", value=0, min=0, step=1
                ).classes("w-40")

            with ui.row().classes("gap-2 q-mb-md"):
                async def preview_setup():
                    if state.rdsr_df is None:
                        ui.notify("Load an RDSR file first", type="warning")
                        return
                    geom_spinner.visible = True
                    fig = await run.io_bound(_make_geometry_fig, "plot_setup", 0)
                    geom_spinner.visible = False
                    if fig:
                        geom_plot.update_figure(fig)
                    else:
                        ui.notify("Geometry preview failed — check console", type="negative")

                async def preview_event():
                    if state.rdsr_df is None:
                        ui.notify("Load an RDSR file first", type="warning")
                        return
                    geom_spinner.visible = True
                    fig = await run.io_bound(_make_geometry_fig, "plot_event", int(geom_event_input.value or 0))
                    geom_spinner.visible = False
                    if fig:
                        geom_plot.update_figure(fig)
                    else:
                        ui.notify("Geometry preview failed — check console", type="negative")

                async def preview_procedure():
                    if state.rdsr_df is None:
                        ui.notify("Load an RDSR file first", type="warning")
                        return
                    geom_spinner.visible = True
                    fig = await run.io_bound(_make_geometry_fig, "plot_procedure", 0)
                    geom_spinner.visible = False
                    if fig:
                        geom_plot.update_figure(fig)
                    else:
                        ui.notify("Geometry preview failed — check console", type="negative")

                ui.button("Setup view", on_click=preview_setup).props("outline")
                ui.button("Single event", on_click=preview_event).props("outline")
                ui.button("Full procedure", on_click=preview_procedure).props("outline")

            geom_spinner = ui.spinner(size="lg").classes("q-mb-sm")
            geom_spinner.visible = False

            geom_plot = ui.plotly({}).classes("w-full").style("height:600px")

        # ══════════════════════════════════════════════════════════════════
        # TAB 3 — SETTINGS
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("settings"):
            ui.label("Calculation Settings").classes("text-h6 q-mb-md")

            with ui.expansion("Phantom", icon="person", value=True).classes("w-full q-mb-sm"):
                with ui.column().classes("w-full gap-2"):
                    ui.select(PHANTOM_MODELS, label="Phantom model", value=state.phantom_model).bind_value(
                        state, "phantom_model"
                    ).on("update:model-value", reset_results).classes("w-full")

                    mesh_select = ui.select(
                        HUMAN_MESHES, label="Human mesh", value=state.human_mesh
                    ).bind_value(state, "human_mesh").on("update:model-value", reset_results).classes("w-full")

                    # show/hide mesh selector based on model
                    def _update_mesh_visibility():
                        mesh_select.visible = state.phantom_model == "human"

                    ui.timer(0.5, _update_mesh_visibility)

                    ui.select(ORIENTATIONS, label="Patient orientation", value=state.patient_orientation).bind_value(
                        state, "patient_orientation"
                    ).on("update:model-value", reset_results).classes("w-full")

                    with ui.row().classes("gap-4"):
                        ui.number(label="Offset d_lon (cm)", value=state.d_lon, step=1.0).bind_value(
                            state, "d_lon"
                        ).on("update:model-value", reset_results).classes("w-32")
                        ui.number(label="Offset d_ver (cm)", value=state.d_ver, step=1.0).bind_value(
                            state, "d_ver"
                        ).on("update:model-value", reset_results).classes("w-32")
                        ui.number(label="Offset d_lat (cm)", value=state.d_lat, step=1.0).bind_value(
                            state, "d_lat"
                        ).on("update:model-value", reset_results).classes("w-32")

            with ui.expansion("Physics", icon="science").classes("w-full q-mb-sm"):
                with ui.column().classes("w-full gap-3"):
                    est_cb = ui.checkbox("Use estimated table transmission (k_tab)", value=state.estimate_k_tab).bind_value(
                        state, "estimate_k_tab"
                    ).on("update:model-value", reset_results)

                    with ui.row().classes("items-center gap-4"):
                        ui.label("k_tab value:").classes("text-caption")
                        ui.slider(min=0.0, max=1.0, step=0.01, value=state.k_tab_val).bind_value(
                            state, "k_tab_val"
                        ).on("update:model-value", reset_results).classes("w-48")
                        ktab_display = ui.label(f"{state.k_tab_val:.2f}").classes("text-caption w-10")
                        ui.timer(0.3, lambda: ktab_display.set_text(f"{state.k_tab_val:.2f}"))

                    ui.number(
                        label="Inherent filtration (mmAl)", value=state.inherent_filtration, min=0.0, step=0.1
                    ).bind_value(state, "inherent_filtration").on("update:model-value", reset_results).classes("w-56")

                    ui.checkbox("Remove rows with kVp = 0", value=state.remove_invalid_rows).bind_value(
                        state, "remove_invalid_rows"
                    ).on("update:model-value", reset_results)

            with ui.expansion("Display", icon="palette").classes("w-full q-mb-sm"):
                with ui.column().classes("w-full gap-2"):
                    ui.checkbox("Show dose map after calculation", value=state.plot_dosemap).bind_value(
                        state, "plot_dosemap"
                    )
                    ui.select(COLORSCALES, label="Dose map colorscale", value=state.colorscale).bind_value(
                        state, "colorscale"
                    ).classes("w-48")

        # ══════════════════════════════════════════════════════════════════
        # TAB 4 — CALCULATE
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("calculate"):
            ui.label("Run Dose Calculation").classes("text-h6 q-mb-md")

            # settings summary card
            with ui.card().classes("w-full q-mb-md"):
                ui.label("Current settings").classes("text-subtitle2 q-mb-xs")
                calc_summary = ui.label("").classes("text-caption text-grey-6")

                def _refresh_summary():
                    if state.rdsr_df is None:
                        calc_summary.set_text("No file loaded.")
                        return
                    calc_summary.set_text(
                        f"File: {state.file_name}  |  Events: {len(state.rdsr_df)}  |  "
                        f"Phantom: {state.phantom_model}"
                        + (f" / {state.human_mesh}" if state.phantom_model == "human" else "")
                        + f"  |  k_tab: {'estimated ' + str(state.k_tab_val) if state.estimate_k_tab else 'measured'}"
                        + f"  |  Filtration: {state.inherent_filtration} mmAl"
                    )

                ui.timer(1.0, _refresh_summary)

            calc_progress = ui.linear_progress(value=0).classes("w-full q-mb-xs")
            calc_progress.visible = False
            calc_status_label = ui.label("").classes("text-caption text-grey-6 q-mb-md")

            async def do_calculate():
                dprint("GUI", "Calculate button clicked")
                if state.rdsr_df is None:
                    ui.notify("Load an RDSR file first (tab 1)", type="warning")
                    return

                calc_btn.disable()
                run_btn_drawer.disable()
                calc_progress.visible = True
                calc_progress.set_value(0)
                calc_status_label.set_text("Starting…")

                def progress_cb(fraction: float, label: str):
                    calc_progress.set_value(fraction)
                    calc_status_label.set_text(label)

                dprint("GUI", "Running calculation via io_bound")
                ok, msg = await run.io_bound(run_calculation, state, progress_cb)

                calc_progress.set_value(1.0)
                calc_btn.enable()
                run_btn_drawer.enable()

                if ok:
                    psd_label.set_text(f"PSD: {state.psd:.2f} mGy")
                    calc_status_label.set_text(f"Done — {msg}")
                    ui.notify(f"✓ {msg}", type="positive")
                    tabs.set_value("results")
                else:
                    calc_status_label.set_text("Calculation failed")
                    ui.notify(f"Error: {msg[:300]}", type="negative", timeout=10000)

            calc_btn = ui.button("▶  Run Calculation", on_click=do_calculate, color="positive").classes(
                "text-h6 q-px-xl q-py-sm"
            )
            run_btn_drawer.on("click", do_calculate)

        # ══════════════════════════════════════════════════════════════════
        # TAB 5 — RESULTS
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("results"):
            ui.label("Results").classes("text-h6 q-mb-md")

            # metric cards
            with ui.row().classes("gap-4 q-mb-md"):
                with ui.card().classes("q-pa-md text-center"):
                    ui.label("Peak Skin Dose").classes("text-caption text-grey-6")
                    psd_metric = ui.label("—").classes("text-h5 text-positive text-bold")

                with ui.card().classes("q-pa-md text-center"):
                    ui.label("Total Air Kerma").classes("text-caption text-grey-6")
                    kerma_metric = ui.label("—").classes("text-h5 text-bold")

                with ui.card().classes("q-pa-md text-center"):
                    ui.label("Events").classes("text-caption text-grey-6")
                    events_metric = ui.label("—").classes("text-h5 text-bold")

            def _refresh_metrics():
                if state.calculation_done and state.psd is not None:
                    psd_metric.set_text(f"{state.psd:.2f} mGy")
                    kerma_metric.set_text(f"{state.air_kerma:.2f} mGy")
                    events_metric.set_text(str(len(state.rdsr_df)))

            ui.timer(1.0, _refresh_metrics)

            # colorscale selector
            with ui.row().classes("items-center gap-3 q-mb-sm"):
                ui.label("Colorscale:").classes("text-caption")
                ui.select(COLORSCALES, value=state.colorscale).bind_value(state, "colorscale").classes(
                    "w-40"
                ).on("update:model-value", lambda: _refresh_dosemap())

            # dose map plot
            dosemap_plot = ui.plotly({}).classes("w-full").style("height:650px")
            dosemap_spinner = ui.spinner(size="lg")
            dosemap_spinner.visible = False

            def _refresh_dosemap():
                if not state.calculation_done:
                    return
                dosemap_spinner.visible = True
                fig = _make_dosemap_fig()
                dosemap_spinner.visible = False
                if fig:
                    dosemap_plot.update_figure(fig)

            ui.timer(1.5, lambda: _refresh_dosemap() if state.calculation_done and state.dosemap_fig is None else None)

            # correction factor table
            ui.label("Correction factors per event").classes("text-subtitle2 q-mt-md q-mb-xs")
            corr_table = ui.table(
                columns=[
                    {"name": "event", "label": "Event", "field": "event", "align": "right"},
                    {"name": "k_isq", "label": "k_isq (mean)", "field": "k_isq", "align": "right"},
                    {"name": "k_bs", "label": "k_bs (mean)", "field": "k_bs", "align": "right"},
                    {"name": "k_med", "label": "k_med", "field": "k_med", "align": "right"},
                    {"name": "k_tab", "label": "k_tab", "field": "k_tab", "align": "right"},
                    {"name": "kerma", "label": "K_IRP (mGy)", "field": "kerma", "align": "right"},
                ],
                rows=[],
                row_key="event",
            ).classes("w-full")

            def _refresh_corr_table():
                if not state.calculation_done or state.output is None:
                    return
                out = state.output
                corrections = out.get("corrections", {})
                hits_list = corrections.get("correction_value_index", [])
                k_isq_list = corrections.get("inverse_square_law", [])
                k_bs_list = corrections.get("backscatter", [])
                k_med_list = corrections.get("medium", [])
                k_tab_list = corrections.get("table", [])
                kerma_list = [out["events"]["beam"] and 0] * len(hits_list)  # fallback

                # kerma per event from raw output
                import numpy as np
                rows = []
                n = len(hits_list)
                for i in range(n):
                    def _mean(lst, i):
                        try:
                            v = lst[i]
                            if hasattr(v, "__len__") and len(v):
                                return round(float(np.mean(v)), 4)
                            return round(float(v), 4) if v else "—"
                        except Exception:
                            return "—"

                    rows.append({
                        "event": i + 1,
                        "k_isq": _mean(k_isq_list, i),
                        "k_bs": _mean(k_bs_list, i),
                        "k_med": _mean(k_med_list, i),
                        "k_tab": _mean(k_tab_list, i),
                        "kerma": "—",
                    })
                corr_table.rows = rows
                corr_table.update()

            ui.timer(2.0, _refresh_corr_table)

        # ══════════════════════════════════════════════════════════════════
        # TAB 6 — EXPORT
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel("export"):
            ui.label("Export Results").classes("text-h6 q-mb-md")

            no_results_note = ui.label(
                "Run a calculation first (tab 4) to enable exports."
            ).classes("text-caption text-grey-6 q-mb-md")

            with ui.card().classes("w-full q-mb-md"):
                ui.label("JSON — full results dict").classes("text-subtitle2 q-mb-xs")
                ui.label(
                    "Contains PSD, air kerma, dose map, correction factors, phantom geometry, and event data."
                ).classes("text-caption text-grey-6 q-mb-sm")

                def download_json():
                    if not state.calculation_done or state.output is None:
                        ui.notify("No results yet", type="warning")
                        return
                    data = json.dumps(state.output, default=str, indent=2).encode()
                    ui.download(data, "mypyskindose_results.json")

                ui.button("Download JSON", on_click=download_json, icon="download").props("outline")

            with ui.card().classes("w-full q-mb-md"):
                ui.label("Interactive HTML dose map").classes("text-subtitle2 q-mb-xs")
                ui.label(
                    "Self-contained HTML file with the interactive 3D Plotly dose map."
                ).classes("text-caption text-grey-6 q-mb-sm")

                async def download_html():
                    if not state.calculation_done:
                        ui.notify("No results yet", type="warning")
                        return
                    html_bytes = await run.io_bound(_make_dosemap_html)
                    if html_bytes:
                        ui.download(html_bytes, "dosemap.html")
                    else:
                        ui.notify("Could not generate HTML", type="negative")

                ui.button("Download HTML", on_click=download_html, icon="download").props("outline")

            with ui.card().classes("w-full q-mb-md"):
                ui.label("PNG dose map (4 views)").classes("text-subtitle2 q-mb-xs")
                ui.label(
                    "Static PNG images from right, back, left, and front camera angles."
                ).classes("text-caption text-grey-6 q-mb-sm")

                async def download_png():
                    if not state.calculation_done:
                        ui.notify("No results yet", type="warning")
                        return
                    png_bytes = await run.io_bound(_make_dosemap_png)
                    if png_bytes:
                        ui.download(png_bytes, "dosemap_right.png")
                    else:
                        ui.notify(
                            "PNG export requires kaleido. Install with: pip install kaleido",
                            type="warning",
                            timeout=6000,
                        )

                ui.button("Download PNG (right view)", on_click=download_png, icon="download").props("outline")

    # ── Restore view if data already loaded ──
    if state.rdsr_df is not None:
        dprint("GUI", "Restoring UI state from loaded data")
        file_label.set_text(f"📁 {state.file_name}")
        events_label.set_text(f"📊 {len(state.rdsr_df)} events")
        _refresh_event_table()
        if hasattr(state, "active_tab") and state.active_tab:
            tabs.set_value(state.active_tab)

# ── figure-building helpers (called via run.io_bound) ─────────────────────

def _make_geometry_fig(mode: str, event_index: int):
    """Build a Plotly Figure for geometry preview. Returns fig dict or None."""
    try:
        import plotly.graph_objects as go
        from mypyskindose.helpers.calculate_rotation_matrices import calculate_rotation_matrices
        from mypyskindose.geom_calc import position_patient_phantom_on_table
        from mypyskindose.phantom_class import Phantom
        from mypyskindose.plotting.create_geometry_plot import create_geometry_plot
        from mypyskindose import constants as c

        settings = build_settings(state, mode=mode, output_format="dict")
        settings.plot.plot_event_index = event_index
        settings.plot.notebook_mode = False
        settings.plot.interactivity = True

        data_norm = calculate_rotation_matrices(state.rdsr_df.copy())

        table = Phantom(phantom_model=c.PHANTOM_MODEL_TABLE, phantom_dim=settings.phantom.dimension)
        pad = Phantom(phantom_model=c.PHANTOM_MODEL_PAD, phantom_dim=settings.phantom.dimension)

        # We need to capture the figure instead of showing it.
        # Monkey-patch fig.show to intercept.
        captured = {}

        original_show = go.Figure.show

        def _capture_show(self, *a, **kw):
            captured["fig"] = self

        go.Figure.show = _capture_show
        try:
            create_geometry_plot(normalized_data=data_norm, table=table, pad=pad, settings=settings)
        finally:
            go.Figure.show = original_show

        fig = captured.get("fig")
        return fig.to_dict() if fig else None
    except Exception as exc:
        import traceback as tb
        print(tb.format_exc())
        return None


def _make_dosemap_fig():
    """Build the dose map Plotly figure from current state.output."""
    try:
        import numpy as np
        import plotly.graph_objects as go
        from mypyskindose.phantom_class import Phantom
        from mypyskindose import constants as c

        if state.output is None:
            return None

        out = state.output
        patient_data = out["patient"]["patient"]
        r = np.array([
            patient_data["patient_skin_cells"]["x"],
            patient_data["patient_skin_cells"]["y"],
            patient_data["patient_skin_cells"]["z"],
        ]).T
        ijk_data = patient_data["triangle_vertex_indices"]
        dose_map = np.zeros(len(r))
        for idx, dose in out["dose_map"]:
            dose_map[int(idx)] = dose

        hover = [
            f"<b>lat:</b> {r[i,2]:.2f} cm<br><b>lon:</b> {r[i,0]:.2f} cm<br>"
            f"<b>ver:</b> {r[i,1]:.2f} cm<br><b>dose:</b> {dose_map[i]:.2f} mGy"
            for i in range(len(r))
        ]

        cmax = float(np.max(dose_map))
        if cmax == 0:
            cmax = 1.0

        mesh = go.Mesh3d(
            x=r[:, 0], y=r[:, 1], z=r[:, 2],
            i=ijk_data["i"], j=ijk_data["j"], k=ijk_data["k"],
            intensity=dose_map,
            intensitymode="vertex",
            colorscale=state.colorscale,
            cmin=0.0,
            cmax=cmax,
            showscale=True,
            hoverinfo="text",
            text=hover,
            colorbar=dict(title=dict(text="Skin dose [mGy]")),
        )

        bg = "rgb(33,33,33)" if state.dark_mode else "rgb(252,252,252)"
        txt = "rgb(252,252,252)" if state.dark_mode else "rgb(52,49,49)"

        layout = go.Layout(
            paper_bgcolor=bg,
            font=dict(color=txt),
            margin=dict(l=0, r=0, b=40, t=40),
            scene=dict(
                aspectmode="data",
                xaxis=dict(title="X - LON [cm]", backgroundcolor=bg, color=txt),
                yaxis=dict(title="Y - VER [cm]", backgroundcolor=bg, color=txt),
                zaxis=dict(title="Z - LAT [cm]", backgroundcolor=bg, color=txt),
            ),
        )
        fig = go.Figure(data=[mesh], layout=layout)
        state.dosemap_fig = fig
        return fig.to_dict()
    except Exception:
        import traceback as tb
        print(tb.format_exc())
        return None


def _make_dosemap_html() -> bytes | None:
    try:
        fig_dict = _make_dosemap_fig()
        if fig_dict is None:
            return None
        import plotly.graph_objects as go
        fig = go.Figure(fig_dict)
        return fig.to_html(full_html=True).encode()
    except Exception:
        return None


def _make_dosemap_png() -> bytes | None:
    try:
        fig_dict = _make_dosemap_fig()
        if fig_dict is None:
            return None
        import plotly.graph_objects as go
        fig = go.Figure(fig_dict)
        fig.update_layout(scene_camera=dict(eye=dict(x=-2.5, y=1.5, z=0)))
        return fig.to_image(format="png")
    except Exception:
        return None


# ── entry point ────────────────────────────────────────────────────────────

def run_gui(native: bool = False) -> None:
    """Launch the MyPySkinDose NiceGUI app."""
    dprint("GUI", f"Starting run_gui, native={native}")
    ui.run(
        title="MyPySkinDose",
        native=native,
        reload=False,
        port=8765,
        show=True,
        favicon="🩻",
        reconnect_timeout=30.0,
    )


if __name__ == "__main__":
    run_gui()
