"""Session-state namespace and Signal Hub mode for Reach Signal's interface."""
import os

NS = "reach"


def k(name: str) -> str:
    """Every session-state key and widget key goes through here, so Reach Signal's state never collides in the Hub."""
    return f"{NS}:{name}"


def hub_mode() -> bool:
    """Signal Hub sets SIGNAL_HUB=1: keep everything in session memory, write no files, make no network calls."""
    return os.environ.get("SIGNAL_HUB") == "1"
