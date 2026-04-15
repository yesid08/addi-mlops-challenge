"""Runtime override store for A/B experiment configuration.

Holds in-memory overrides for AB_TREATMENT_TRAFFIC_PCT and AB_EXPERIMENT_SALT
that take precedence over the env-var defaults read at startup.  Overrides are
process-local and reset on restart, which is intentional for this stage of the
project (production would use Redis or a feature-flag service).

Usage:
    store = ABConfigStore()
    store.set_override(pct=30, salt=None)  # override traffic only
    store.get_pct()   # → 30
    store.get_salt()  # → None  (caller falls back to ab_settings)
    store.clear()     # reverts everything to env-var defaults
"""

import threading


class ABConfigStore:
    """Thread-safe store for runtime A/B configuration overrides."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pct: int | None = None
        self._salt: str | None = None

    def get_pct(self) -> int | None:
        """Return the override traffic percentage, or None if not set."""
        with self._lock:
            return self._pct

    def get_salt(self) -> str | None:
        """Return the override experiment salt, or None if not set."""
        with self._lock:
            return self._salt

    def set_override(self, pct: int | None, salt: str | None) -> None:
        """Set runtime overrides.  Pass None for either field to leave it unchanged."""
        with self._lock:
            if pct is not None:
                self._pct = pct
            if salt is not None:
                self._salt = salt

    def clear(self) -> None:
        """Remove all overrides — both values revert to env-var defaults."""
        with self._lock:
            self._pct = None
            self._salt = None
