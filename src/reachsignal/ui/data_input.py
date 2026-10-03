"""Choose a file, manual entry or an optional AI draft on equal footing."""
import hashlib

import pandas as pd
import streamlit as st

from reachsignal import input_format as fmt, portable as io, spreadsheets as sheets

MODES = ["Excel or CSV", "Enter manually", "Use your AI"]
PAGE = "1 · Add your data"


def navigate(w, mode):
    st.session_state[w.key("page")] = PAGE
    st.session_state[w.key("input_mode")] = mode


def welcome(w):
    st.subheader("Start with what you have")
    st.write("Upload a spreadsheet, enter your own inputs, or let your AI help structure a draft. The fictional demo is already loaded.")
    for col, mode, title in zip(st.columns(3), MODES, ["Upload Excel or CSV", "Enter data manually", "Use your AI"]):
        col.button(title, key=w.key("start:"+mode), on_click=navigate, args=(w, mode), width="stretch")


def templates(w):
    with st.expander("What data do I need? Examples and templates"):
        st.write(fmt.INTRO)
        st.caption(fmt.HELP)
        c1, c2 = st.columns(2)
        c1.download_button("Download simple Excel example", sheets.simple_template(), w.name+"-simple-example.xlsx", sheets.MIME, key=w.key("simple_xlsx"))
        c2.download_button("Download complete Excel example", sheets.project_workbook(w.model, w.model.demo()["data"]), w.name+"-complete-example.xlsx", sheets.MIME, key=w.key("full_xlsx"))
        for key, spec in fmt.QUICK.items():
            st.download_button("CSV example · "+spec["title"], sheets.csv_template(key), w.name+"-"+key+"-example.csv", "text/csv", key=w.key("csv:"+key))
        st.caption("Examples contain fictional data. Replace the example rows with your own. You can use your existing column names and match them after uploading.")
        st.caption("To update an existing case in Excel, download its workbook from Export, edit it, and re-import it as a Complete project workbook.")


def mapping_controls(w, frame, fields, stem):
    mapping = {}
    columns = list(frame.columns)
    cols = st.columns(2)
    for i, (field, (title, kind, aliases)) in enumerate(fields.items()):
        guess = sheets.suggest(columns, [title, field]+aliases)
        required = not kind.startswith("optional_") and kind != "basis"
        options = [None]+columns
        mapping[field] = cols[i % 2].selectbox(title+(" *" if required else ""), options, index=options.index(guess),
            format_func=lambda x: "Choose a column" if x is None else x, key=w.key(stem+":"+field),
            help="Required for each row." if required else "Leave unselected if this is not in your file. Unknown numbers stay blank.")
    return mapping


def source_preview(frame):
    with st.expander(f"Preview source data · {len(frame):,} rows, {len(frame.columns)} columns"):
        st.dataframe(frame.head(30), hide_index=True, width="stretch")


def context_controls(w, stem):
    settings = {}
    if w.name == "learn":
        c1, c2 = st.columns(2)
        settings["unit"] = c1.text_input("Payoff unit", placeholder="e.g. NOK, EUR or utility points", key=w.key(stem+":unit"))
        settings["horizon"] = c2.text_input("Time horizon", placeholder="e.g. contribution over the next 12 months", key=w.key(stem+":horizon"))
        st.caption("Use net payoffs after the cost of each decision. Leave research costs out of these payoffs; studies are compared separately.")
    elif w.name == "reach":
        c1, c2 = st.columns(2)
        settings["demand_unit"] = c1.text_input("What does demand measure?", placeholder="e.g. residents, potential visits or spending", key=w.key(stem+":unit"))
        settings["period"] = c2.text_input("Time period or reference date", placeholder="e.g. October 2026", key=w.key(stem+":period"))
        settings["attractiveness_definition"] = st.text_input("What does site attractiveness measure?", placeholder="e.g. store floor area in square metres, measured consistently", key=w.key(stem+":attraction"))
        st.caption("Population stays population; the app does not turn it into visits or sales. Outside-option weights and attractiveness must use compatible scales.")
        with st.expander("Distance and model assumptions"):
            st.caption("Simple imports use straight-line km. These starting settings are scenario assumptions, not estimates fitted to your data.")
            c1, c2 = st.columns(2)
            settings["alpha"] = c1.number_input("Effect of attractiveness", .1, 5.0, 1.0, key=w.key(stem+":alpha"))
            settings["beta"] = c2.number_input("Effect of distance", 0.0, 5.0, 1.5, key=w.key(stem+":beta"))
            settings["distance_floor"] = c1.number_input("Minimum modeled distance (km)", .000001, 10000.0, .25, key=w.key(stem+":floor"))
            settings["access_threshold"] = c2.number_input("Access threshold (km)", .000001, 10000.0, 5.0, key=w.key(stem+":threshold"))
    return settings


def spreadsheet_input(w):
    templates(w)
    uploads = st.file_uploader("Upload your Excel workbook or CSV files", type=["xlsx", "csv"], accept_multiple_files=True, key=w.key("spreadsheets"))
    st.caption("Excel can contain several sheets. For separate CSV tables, select the files together. Files stay in this session until you save a project; nothing is sent to an AI.")
    if not uploads:
        return
    files = [(u.name, u.getvalue()) for u in uploads]
    fingerprint = hashlib.sha256(b"".join(name.encode()+raw for name, raw in files)).hexdigest()[:20]
    cache = st.session_state.get(w.key("parsed_spreadsheet"))
    if cache is None or cache[0] != fingerprint:
        cache = (fingerprint, sheets.load_tables(files))
        st.session_state[w.key("parsed_spreadsheet")] = cache
    tables = cache[1]
    full_guess = "Case" in tables and all(fmt.TABLE_NAMES[k] in tables for k in w.model.TITLES)
    layout = st.radio("File layout", ["Simple business tables", "Complete project workbook"], index=int(full_guess), horizontal=True, key=w.key("layout:"+fingerprint), help="Use Simple for ordinary business tables with names. Complete uses linked reference columns for every model input.")
    stem = fingerprint+":"+layout
    comma = st.selectbox("Decimal separator in text values", ["Dot (1.5)", "Comma (1,5)"], key=w.key(stem+":decimal")).startswith("Comma")
    default_brief = ""
    if layout == "Complete project workbook" and "Case" in tables and "Case brief" in tables["Case"] and not tables["Case"].empty:
        default_brief = str(tables["Case"].iloc[0]["Case brief"] or "")
    brief = st.text_area("What question should these data help answer?", value=default_brief, placeholder="Describe your business question and the scope of these inputs.", max_chars=2500, key=w.key(stem+":brief"))
    settings = context_controls(w, stem) if layout == "Simple business tables" else {}
    st.subheader("Match your sheets and columns")
    st.caption("Suggestions use column names. Check each selection; unselected columns are not imported. Empty numeric cells stay unknown.")
    mapped, errors, selected = {}, [], []
    names = list(tables)
    if layout == "Simple business tables":
        specs = fmt.QUICK
    else:
        specs = {name: {"title": fmt.TABLE_NAMES[name], "aliases": [name], "fields": {
            field: (sheets.label(field), "optional_text" if "anyOf" in spec or spec.get("type") == "string" and "minLength" not in spec and "pattern" not in spec and "format" not in spec else "text", [])
            for field, spec in w.model.SCHEMA["properties"][name]["items"]["properties"].items()}}
            for name in w.model.TITLES}
    for name, spec in specs.items():
        guess = sheets.suggest(names, [spec["title"], name]+spec["aliases"])
        usable = [n for n in names if sheets.normalize(n) != "case"]
        if guess is None and len(specs) == 1 and len(usable) == 1:
            guess = usable[0]
        with st.expander(spec["title"], expanded=layout == "Simple business tables"):
            if layout == "Complete project workbook":
                st.caption(w.model.TITLES[name])
            chosen = st.selectbox("Sheet / table for "+spec["title"], [None]+names, index=([None]+names).index(guess),
                format_func=lambda x: "Not supplied" if x is None else x, key=w.key(stem+":sheet:"+name))
            if chosen is None:
                if layout == "Simple business tables":
                    errors.append("Choose the sheet or CSV for "+spec["title"]+".")
                continue
            selected.append(chosen)
            frame = tables[chosen]
            source_preview(frame)
            mapping = mapping_controls(w, frame, spec["fields"], stem+":map:"+name+":"+chosen)
            try:
                mapped[name] = (sheets.mapped_rows(frame, mapping, spec["fields"], comma, spec["title"]) if layout == "Simple business tables"
                                else sheets.schema_rows(w.model, name, frame, mapping, comma))
            except io.DataProblem as exc:
                errors.append(str(exc))
    if len(selected) != len(set(selected)):
        errors.append("A sheet is selected more than once. Choose a separate table for each part of the model.")
    if not brief.strip():
        errors.append("Add your business question above.")
    if any(isinstance(value, str) and not value.strip() for value in settings.values()):
        errors.append("Fill in the units and time period above so the numbers have a clear meaning.")
    source = ", ".join(name for name, _ in files)
    candidate = None
    if not errors:
        try:
            candidate = (fmt.build(brief, mapped, settings, source) if layout == "Simple business tables"
                         else sheets.complete_project(w.model, brief, mapped))
        except io.DataProblem as exc:
            errors.append(str(exc))
    st.subheader("Check before importing")
    if errors:
        for error in errors:
            st.warning(error)
        st.caption("Your current project is unchanged. Correct the highlighted inputs and the preview will update.")
        return
    st.success("The file structure is ready. Check the preview, then review the assumptions in Edit & review.")
    st.dataframe(pd.DataFrame([{"Part": fmt.TABLE_NAMES[k], "Rows": len(candidate[k])} for k in w.model.TITLES]), hide_index=True, width="stretch")
    with st.expander("Preview the data that will be used"):
        for name in w.model.TITLES:
            if candidate[name]:
                st.markdown("**"+fmt.TABLE_NAMES[name]+"**")
                st.dataframe(pd.DataFrame(candidate[name]).rename(columns={c: sheets.label(c) for c in candidate[name][0]}), hide_index=True, width="stretch")
    if hasattr(w.model, "readiness"):
        missing = w.model.readiness(candidate)
        if missing:
            st.info("You can import this draft, but more inputs are needed before calculating: " + "; ".join(missing[:5]))
    st.caption("Importing replaces the current case and clears its review. Save the current case from Export if needed. Example rows must be replaced before drawing business conclusions.")
    if st.button("Use these data", type="primary", key=w.key("use_spreadsheet")):
        w.put(io.project(w.name, candidate, ("Spreadsheet draft · "+source)[:200]))
        st.session_state[w.key("next_page")] = "2 · Edit & review"
        st.rerun()


def render(w):
    mode = st.radio("How would you like to add your data?", MODES, horizontal=True, key=w.key("input_mode"))
    if mode == "Excel or CSV":
        spreadsheet_input(w)
    elif mode == "Use your AI":
        st.caption("Optional: use AI to structure notes or research into a draft. You can edit the draft here or export it to Excel for further work.")
        w.ai()
    else:
        st.write("Start a new case, then fill in its tables in Edit & review. No file or AI is required.")
        with st.form(w.key("manual_start")):
            brief = st.text_area("Your business question", max_chars=2500, placeholder="What decision or service would you like to explore?")
            st.caption("This replaces the current session's case. Save it from Export first if needed.")
            if st.form_submit_button("Start entering my data", type="primary"):
                w.put(io.project(w.name, w.model.validate(w.model.starter(brief)), "Manually entered case"))
                st.session_state[w.key("next_page")] = "2 · Edit & review"
                st.rerun()
        st.button("Continue editing the current case", key=w.key("continue_edit"), on_click=lambda: st.session_state.update({w.key("page"): "2 · Edit & review"}))
