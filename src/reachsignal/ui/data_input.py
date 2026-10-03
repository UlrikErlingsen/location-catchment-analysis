"""Choose a file, manual entry or an optional AI draft on equal footing."""
import hashlib

import pandas as pd
import streamlit as st

from reachsignal import input_format as fmt, model, portable as io, spreadsheets as sheets
from reachsignal.ui.keys import hub_mode, k

MODES = ["Excel or CSV", "Enter manually", "Use your AI"]
PAGE = "1 · Add your data"
PREVIEW_ROWS = 1_000


def navigate(mode):
    st.session_state[k("page")] = PAGE
    st.session_state[k("input_mode")] = mode


def welcome(w):
    st.subheader("Start with what you have")
    st.write("Upload a spreadsheet, enter your own inputs, or let your AI help structure a draft. The fictional demo is already loaded.")
    for col, mode, title in zip(st.columns(3), MODES, ["Upload Excel or CSV", "Enter data manually", "Use your AI"]):
        col.button(title, key=k("start:"+mode), on_click=navigate, args=(mode,), width="stretch")


def templates(w):
    with st.expander("What data do I need? Examples and templates"):
        st.write(fmt.INTRO)
        st.caption(fmt.HELP)
        c1, c2 = st.columns(2)
        c1.download_button("Download simple Excel example", sheets.simple_template, w.name+"-simple-example.xlsx", sheets.MIME, key=k("simple_xlsx"))
        c2.download_button("Download complete Excel example", lambda: sheets.project_workbook(model, model.demo()["data"]), w.name+"-complete-example.xlsx", sheets.MIME, key=k("full_xlsx"))
        for key, spec in fmt.QUICK.items():
            st.download_button("CSV example · "+spec["title"], sheets.csv_template(key), w.name+"-"+key+"-example.csv", "text/csv", key=k("csv:"+key))
        st.caption("Examples contain fictional data. Replace the example rows with your own. You can use your existing column names and match them after uploading.")
        st.caption("To update an existing case in Excel, download its workbook from Export, edit it, and re-import it as a Complete project workbook.")


def mapping_controls(frame, fields, stem):
    mapping = {}
    columns = list(frame.columns)
    cols = st.columns(2)
    for i, (field, (title, kind, aliases)) in enumerate(fields.items()):
        guess = sheets.suggest(columns, [title, field]+aliases)
        required = not kind.startswith("optional_") and kind != "basis"
        options = [None]+columns
        mapping[field] = cols[i % 2].selectbox(title+(" *" if required else ""), options, index=options.index(guess),
            format_func=lambda x: "Choose a column" if x is None else x, key=k(stem+":"+field),
            help="Required for each row." if required else "Leave unselected if this is not in your file. Unknown numbers stay blank.")
    return mapping


def source_preview(frame):
    with st.expander(f"Preview source data · {len(frame):,} rows, {len(frame.columns)} columns"):
        st.dataframe(frame.head(30), hide_index=True, width="stretch")


def context_controls(stem):
    settings = {}
    c1, c2 = st.columns(2)
    settings["demand_unit"] = c1.text_input("What does demand measure?", placeholder="e.g. residents, potential visits or spending", key=k(stem+":unit"))
    settings["period"] = c2.text_input("Time period or reference date", placeholder="e.g. October 2026", key=k(stem+":period"))
    settings["attractiveness_definition"] = st.text_input("What does site attractiveness measure?", placeholder="e.g. store floor area in square metres, measured consistently", key=k(stem+":attraction"))
    st.caption("Population stays population; the app does not turn it into visits or sales. Outside-option weights and attractiveness must use compatible scales.")
    with st.expander("Distance and model assumptions"):
        st.caption("Simple imports use straight-line km. These starting settings are scenario assumptions, not estimates fitted to your data.")
        c1, c2 = st.columns(2)
        settings["alpha"] = c1.number_input("Effect of attractiveness", .1, 5.0, 1.0, key=k(stem+":alpha"))
        settings["beta"] = c2.number_input("Effect of distance", 0.0, 5.0, 1.5, key=k(stem+":beta"))
        settings["distance_floor"] = c1.number_input("Minimum modeled distance (km)", .000001, 10000.0, .25, key=k(stem+":floor"))
        settings["access_threshold"] = c2.number_input("Access threshold (km)", .000001, 10000.0, 5.0, key=k(stem+":threshold"))
    return settings


def _fingerprint(uploads):
    """Identify the uploaded set without re-reading large files on every rerun when Streamlit gives each file an id."""
    digest = hashlib.sha256()
    for upload in uploads:
        digest.update(upload.name.encode())
        file_id = getattr(upload, "file_id", None)
        digest.update(str(file_id).encode() if file_id else upload.getvalue())
    return digest.hexdigest()[:20]


def _memo(name, signature, compute):
    """Remember the last mapping result per table, so changing one choice does not re-convert every large table."""
    store = st.session_state.setdefault(k("import_memo"), {})
    if store.get(name, (None,))[0] != signature:
        try:
            store[name] = (signature, compute(), None)
        except io.DataProblem as exc:
            store[name] = (signature, None, str(exc))
    return store[name][1], store[name][2]


def spreadsheet_input(w):
    templates(w)
    uploads = st.file_uploader("Upload your Excel workbook or CSV files", type=["xlsx", "csv"], accept_multiple_files=True, key=k("spreadsheets"))
    st.caption("Excel can contain several sheets. For separate CSV tables, select the files together. Files stay in this session's memory; nothing is written to disk or sent to an AI.")
    st.caption(f"Limits: {sheets.MAX_BYTES // 1_000_000:,} MB per upload, {sheets.MAX_ROWS:,} rows per sheet or CSV, {model.MAX_AREAS:,} customer areas, "
               f"{model.MAX_SITES:,} locations, {model.MAX_DISTANCES:,} travel-time pairs, and areas × locations up to {model.MAX_PAIRS:,}. "
               "CSV reads faster than Excel for very large tables." + (" Signal Hub may set a lower upload limit." if hub_mode() else ""))
    if not uploads:
        return
    fingerprint = _fingerprint(uploads)
    cache = st.session_state.get(k("parsed_spreadsheet"))
    if cache is None or cache[0] != fingerprint:
        st.session_state.pop(k("import_memo"), None)
        cache = (fingerprint, sheets.load_tables([(u.name, u.getvalue()) for u in uploads]))
        st.session_state[k("parsed_spreadsheet")] = cache
    tables = cache[1]
    full_guess = "Case" in tables and all(fmt.TABLE_NAMES[t] in tables for t in model.TITLES)
    layout = st.radio("File layout", ["Simple business tables", "Complete project workbook"], index=int(full_guess), horizontal=True, key=k("layout:"+fingerprint), help="Use Simple for ordinary business tables with names. Complete uses linked reference columns for every model input.")
    stem = fingerprint+":"+layout
    comma = st.selectbox("Decimal separator in text values", ["Dot (1.5)", "Comma (1,5)"], key=k(stem+":decimal")).startswith("Comma")
    default_brief = ""
    if layout == "Complete project workbook" and "Case" in tables and "Case brief" in tables["Case"] and not tables["Case"].empty:
        default_brief = str(tables["Case"].iloc[0]["Case brief"] or "")
    brief = st.text_area("What question should these data help answer?", value=default_brief, placeholder="Describe your business question and the scope of these inputs.", max_chars=2500, key=k(stem+":brief"))
    settings = context_controls(stem) if layout == "Simple business tables" else {}
    st.subheader("Match your sheets and columns")
    st.caption("Suggestions use column names. Check each selection; unselected columns are not imported. Empty numeric cells stay unknown.")
    mapped, errors, selected, signature = {}, [], [], [stem, comma]
    names = list(tables)
    if layout == "Simple business tables":
        specs = fmt.QUICK
    else:
        specs = {name: {"title": fmt.TABLE_NAMES[name], "aliases": [name], "fields": {
            field: (sheets.label(field), "optional_text" if "anyOf" in spec or spec.get("type") == "string" and "minLength" not in spec and "pattern" not in spec and "format" not in spec else "text", [])
            for field, spec in model.SCHEMA["properties"][name]["items"]["properties"].items()}}
            for name in model.TITLES}
    for name, spec in specs.items():
        guess = sheets.suggest(names, [spec["title"], name]+spec["aliases"])
        usable = [n for n in names if sheets.normalize(n) != "case"]
        if guess is None and len(specs) == 1 and len(usable) == 1:
            guess = usable[0]
        with st.expander(spec["title"], expanded=layout == "Simple business tables"):
            if layout == "Complete project workbook":
                st.caption(model.TITLES[name])
            chosen = st.selectbox("Sheet / table for "+spec["title"], [None]+names, index=([None]+names).index(guess),
                format_func=lambda x: "Not supplied" if x is None else x, key=k(stem+":sheet:"+name))
            if chosen is None:
                if layout == "Simple business tables":
                    errors.append("Choose the sheet or CSV for "+spec["title"]+".")
                continue
            selected.append(chosen)
            frame = tables[chosen]
            source_preview(frame)
            mapping = mapping_controls(frame, spec["fields"], stem+":map:"+name+":"+chosen)
            key = (stem, comma, chosen, tuple(mapping.items()))
            signature.append((name, key))
            rows, error = _memo(name, key, lambda: (
                sheets.mapped_rows(frame, mapping, spec["fields"], comma, spec["title"]) if layout == "Simple business tables"
                else sheets.schema_rows(model, name, frame, mapping, comma)))
            if error:
                errors.append(error)
            else:
                mapped[name] = rows
    if len(selected) != len(set(selected)):
        errors.append("A sheet is selected more than once. Choose a separate table for each part of the model.")
    if not brief.strip():
        errors.append("Add your business question above.")
    if any(isinstance(value, str) and not value.strip() for value in settings.values()):
        errors.append("Fill in the units and time period above so the numbers have a clear meaning.")
    source = ", ".join(u.name for u in uploads)
    candidate = None
    if not errors:
        signature += [brief, tuple(settings.items()), source]
        candidate, error = _memo("_case", tuple(signature), lambda: (
            fmt.build(brief, mapped, settings, source) if layout == "Simple business tables"
            else sheets.complete_project(model, brief, mapped)))
        if error:
            errors.append(error)
    st.subheader("Check before importing")
    if errors:
        for error in errors:
            st.warning(error)
        st.caption("Your current project is unchanged. Correct the highlighted inputs and the preview will update.")
        return
    st.success("The file structure is ready. Check the preview, then review the assumptions in Edit & review.")
    st.dataframe(pd.DataFrame([{"Part": fmt.TABLE_NAMES[t], "Rows": len(candidate[t])} for t in model.TITLES]), hide_index=True, width="stretch")
    with st.expander("Preview the data that will be used"):
        for name in model.TITLES:
            if candidate[name]:
                st.markdown("**"+fmt.TABLE_NAMES[name]+"**")
                st.dataframe(pd.DataFrame(candidate[name][:PREVIEW_ROWS]).rename(columns=sheets.label), hide_index=True, width="stretch")
                if len(candidate[name]) > PREVIEW_ROWS:
                    st.caption(f"First {PREVIEW_ROWS:,} of {len(candidate[name]):,} rows. Every row is imported.")
    count, missing = model.readiness_summary(candidate, limit=5)
    if count:
        st.info(f"You can import this draft, but {count:,} more input(s) are needed before calculating, for example: " + "; ".join(missing))
    st.caption("Importing replaces the current case and clears its review. Save the current case from Export if needed. Example rows must be replaced before drawing business conclusions.")
    if st.button("Use these data", type="primary", key=k("use_spreadsheet")):
        w.put(io.project(w.name, candidate, ("Spreadsheet draft · "+source)[:200]))
        for name in ("parsed_spreadsheet", "import_memo"):
            st.session_state.pop(k(name), None)
        st.session_state[k("next_page")] = "2 · Edit & review"
        st.rerun()


def render(w):
    mode = st.radio("How would you like to add your data?", MODES, horizontal=True, key=k("input_mode"))
    if mode == "Excel or CSV":
        spreadsheet_input(w)
    elif mode == "Use your AI":
        st.caption("Optional: use AI to structure notes or research into a draft. You can edit the draft here or export it to Excel for further work.")
        w.ai()
    else:
        st.write("Start a new case, then fill in its tables in Edit & review. No file or AI is required.")
        with st.form(k("manual_start")):
            brief = st.text_area("Your business question", max_chars=2500, placeholder="What decision or service would you like to explore?", key=k("manual_brief"))
            st.caption("This replaces the current session's case. Save it from Export first if needed.")
            if st.form_submit_button("Start entering my data", type="primary", key=k("manual_submit")):
                w.put(io.project(w.name, model.validate(model.starter(brief)), "Manually entered case"))
                st.session_state[k("next_page")] = "2 · Edit & review"
                st.rerun()
        st.button("Continue editing the current case", key=k("continue_edit"), on_click=lambda: st.session_state.update({k("page"): "2 · Edit & review"}))
