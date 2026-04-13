"""Deterministic A/B traffic split for the handle_general experiment.

Algorithm: SHA-256 hash of "{salt}:{user_id}" → first 8 hex digits → int → mod 100.
If the resulting bucket is less than `ab_treatment_traffic_pct`, the user gets variant B.
Otherwise they get variant A.

Using SHA-256 (not Python's built-in hash()) guarantees stable assignments across
process restarts, Python versions, and machines — Python's hash() is randomised by
PYTHONHASHSEED and would produce different variants on every restart.
"""

import hashlib
import logging
from typing import Any, Literal

from deliverables.part2_ab_testing.ab_config import ab_settings


def assign_variant(
    user_id: str,
    *,
    pct: int | None = None,
    salt: str | None = None,
) -> Literal["A", "B"]:
    """Return the variant ("A" or "B") assigned to this user.

    The assignment is deterministic: the same (user_id, pct, salt) always
    returns the same variant.  This guarantees that a user sees the same
    agent version throughout an experiment session.

    Args:
        user_id: The user's identifier (e.g. "user_001").
        pct:     Override for AB_TREATMENT_TRAFFIC_PCT (useful in tests).
        salt:    Override for AB_EXPERIMENT_SALT (useful in tests).
    """
    _pct = pct if pct is not None else ab_settings.ab_treatment_traffic_pct
    _salt = salt if salt is not None else ab_settings.ab_experiment_salt

    key = f"{_salt}:{user_id}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return "B" if bucket < _pct else "A"


def get_graph_for_variant(variant: str, app_state: Any) -> Any:
    """Return the pre-compiled graph that corresponds to the given variant.

    Args:
        variant:   "A" or "B".
        app_state: The FastAPI ``app.state`` object (holds graph_a and graph_b).
    """
    return app_state.graph_b if variant == "B" else app_state.graph_a


def log_assignment(
    user_id: str,
    variant: str,
    correlation_id: str,
    logger: logging.Logger,
) -> None:
    """Emit a structured log line recording the variant assignment."""
    logger.info(
        "ab_variant=%s user_id=%s correlation_id=%s",
        variant,
        user_id,
        correlation_id,
    )
