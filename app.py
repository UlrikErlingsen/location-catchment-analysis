"""Standalone Reach Signal entry point."""
import os
from pathlib import Path
import sys

os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
from reachsignal.ui import render, signal_theme as sig

st.set_page_config(**sig.page_config("reach"))
render()
