# Changelog

All notable changes to Reach Signal are documented here.

## [1.1.0] - 2026-10-03

### Changed

- **No data limits on your own computer.** Standalone, in a local Signal Hub or on a company server, Reach Signal no longer caps upload size, rows, cells, customer areas, locations, travel-time pairs or areas × locations; memory is the limit. The 1.0 caps are gone.
- **Public demo caps.** With `SIGNAL_PUBLIC=1` the app applies hard caps for a shared server (50 MB uploads, 200,000 rows per sheet, 2 million cells, 50,000 areas, 100 locations, 200,000 travel-time pairs, 2 million areas × locations, 50 MB JSON, 2 million pasted characters), all defined in `reachsignal/limits.py`. Capped messages say it is a demo limit.
- Upload cap raised to 10,000 MB in `.streamlit/config.toml`, the launchers (`REACHSIGNAL_MAX_UPLOAD_MB`) and the Dockerfile.

### Added

- Running out of memory is reported as a plain message instead of an error trace.
- The Evidence ZIP holds the full area × location allocation table, written block by block. Excel tables longer than one sheet continue on "(cont. N)" sheets, and the importer joins them again.

## [1.0.0] - 2026-10-03

First public release.

### Added

- **Huff catchment model:** `A^α / max(d, floor)^β` with an explicit outside option per customer area, on straight-line (Haversine) kilometres or a complete matrix of travel minutes. Demand is fixed and conserved across scenarios.
- **Candidate comparison:** each candidate is added to the same baseline on its own, with its allocation and the change for existing own sites, competitors and the outside option; all candidates are computed in one pass. A distance-decay sensitivity check repeats the comparison for β from 0.5 to 3.0.
- **Access:** demand beyond a chosen distance from any listed site, in the baseline and with each candidate.
- **Large cases:** up to 500,000 customer areas, 500 locations, 1,000,000 travel-time pairs and 25 million area × location pairs. The engine works in blocks of areas, validation runs column by column, and results are computed once per change. A 200,000-area × 50-location case is modeled in seconds with a process peak around 630 MB. The map aggregates areas into a grid above 3,000 areas, and long tables and the printable brief show their first or largest rows, each with a note.
- **Data input on equal footing:** simple Excel/CSV tables with column matching, a complete project workbook with travel times, manual entry, and an optional copy-and-paste AI prompt. Uploads up to 1,000 MB. Blank numbers stay unknown and block calculation; nothing is filled in silently.
- **Review gate:** results appear only after a named review tied to a SHA-256 fingerprint of the inputs; every edit clears it.
- **Exports:** Excel workbook (re-importable), project JSON, printable HTML brief and evidence ZIP, built on click, with spreadsheet-formula neutralisation.
- Fictional Oslo-area café demo, Research & limits page with verified sources and interpretation boundaries.
- Signal Hub entry point `reachsignal.ui.render()` with `APP_INFO`, `reach:`-namespaced keys and Hub mode (no file writes, no network calls, opens on the fictional demo).
- Windows and macOS launchers (port 8599, `REACHSIGNAL_PORT`, `REACHSIGNAL_MAX_UPLOAD_MB` default 1000), Dockerfile, `AI_ANALYST.md`, data guide, methods and sources documentation.
