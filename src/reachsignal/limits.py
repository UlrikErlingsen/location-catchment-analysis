"""Data limits: none on your own computer, hard caps on a public demo (SIGNAL_PUBLIC=1).

Run locally, standalone or inside a company's own Signal Hub, Reach Signal imposes no limits on file size, rows,
cells, areas or locations: the computer's memory is the limit. A public demo on a shared server sets
SIGNAL_PUBLIC=1, and then the caps below apply. Every cap lives here, so the rest of the app asks `cap(name)`.
"""
import os

# Caps for a shared demo server with about 4 GB of memory. None of them applies outside SIGNAL_PUBLIC=1.
DEMO = {
    "upload_mb": 50,            # bytes across the files of one upload
    "json_mb": 50,              # a project or AI JSON file
    "paste_chars": 2_000_000,   # pasted AI replies
    "notes_chars": 35_000,      # source notes pasted into the AI prompt
    "rows": 200_000,            # rows per sheet or CSV
    "columns": 80,              # columns per sheet or CSV
    "sheets": 30,               # sheets per workbook
    "cells": 2_000_000,         # cells across one upload
    "unzipped_mb": 500,         # opened size of an .xlsx
    "areas": 50_000,            # customer areas in a case
    "sites": 100,               # locations (all roles) in a case
    "distances": 200_000,       # travel-time pairs in a case
    "pairs": 2_000_000,         # customer areas x locations evaluated by the model
}


def public() -> bool:
    return os.environ.get("SIGNAL_PUBLIC") == "1"


def cap(name: str):
    """The demo cap for `name` on a public demo, otherwise None (no limit)."""
    return DEMO[name] if public() else None


def over(name: str, value) -> bool:
    limit = cap(name)
    return limit is not None and value > limit


def demo_limit(text: str) -> str:
    return f"{text} This is a limit of the public demo; the downloaded app has no data limits."


OUT_OF_MEMORY = ("There is not enough memory for this on this computer. Close other programs and try again, use CSV "
                 "instead of Excel, or aggregate small areas (for example postcodes into districts).")
