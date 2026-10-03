from reachsignal import __version__
from reachsignal.ui.app import render
from reachsignal.ui import signal_theme

APP_INFO = {"product": "Reach Signal", "version": __version__, "repo": "location-catchment-analysis", "slug": "reach"}
__all__ = ["render", "signal_theme", "APP_INFO"]
