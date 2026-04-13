"""In-memory feedback store with per-variant aggregation and a live z-test.

Users signal satisfaction by rating a conversation "good" or "bad" (analogous to
thumbs-up / thumbs-down in ChatGPT).  Each entry is tagged with the A/B variant
that served the conversation so that the adoption metric can be compared between
Version A (control) and Version B (treatment).

Thread safety: all mutations are guarded by a single threading.Lock so the store
can be used safely under ASGI's single-process concurrency model.

Production note: this store is in-memory only — data is lost on restart.  Replace
with a time-series DB (e.g. InfluxDB) or a relational table for durable storage.
"""

import math
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


@dataclass
class FeedbackEntry:
    conversation_id: str
    user_id: str
    ab_variant: str
    rating: Literal["good", "bad"]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def _two_proportion_z_test(
    good_a: int,
    total_a: int,
    good_b: int,
    total_b: int,
    min_samples: int = 10,
) -> dict[str, Any] | None:
    """Compute a two-proportion z-test for adoption rates.

    Returns None when either variant has fewer than `min_samples` feedback entries
    (insufficient data for a meaningful result).

    The p-value is computed from the standard normal CDF via math.erfc, which
    avoids a scipy dependency:
        p_value = erfc(|z| / sqrt(2))   (two-tailed)

    Returns a dict with: z_statistic, p_value, significant (p < 0.05), note.
    """
    if total_a < min_samples or total_b < min_samples:
        return None

    p_a = good_a / total_a
    p_b = good_b / total_b
    p_pool = (good_a + good_b) / (total_a + total_b)

    # Guard against degenerate cases (all good or all bad across both variants).
    if p_pool in (0.0, 1.0):
        return {
            "z_statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "note": "No variance in pooled proportion — cannot compute z-test.",
        }

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / total_a + 1 / total_b))
    if se == 0.0:
        return {
            "z_statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "note": "Standard error is zero — cannot compute z-test.",
        }

    z = (p_b - p_a) / se
    # erfc(|z| / sqrt(2)) gives the two-tailed p-value for the standard normal.
    p_value = math.erfc(abs(z) / math.sqrt(2))

    return {
        "z_statistic": round(z, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "note": (
            f"Two-proportion z-test | p_A={p_a:.3f} ({total_a} ratings) "
            f"| p_B={p_b:.3f} ({total_b} ratings)"
        ),
    }


class FeedbackStore:
    """Thread-safe in-memory store for user feedback entries."""

    def __init__(self) -> None:
        self._entries: list[FeedbackEntry] = []
        self._lock = threading.Lock()

    def record(self, entry: FeedbackEntry) -> None:
        """Append a feedback entry."""
        with self._lock:
            self._entries.append(entry)

    def get_summary(self) -> dict[str, Any]:
        """Return per-variant counts, good-rates, and a live two-proportion z-test.

        The statistical_test field is None when either variant has fewer than
        10 feedback entries (insufficient data).
        """
        with self._lock:
            entries = list(self._entries)

        counts: dict[str, dict[str, int]] = {
            "A": {"good": 0, "bad": 0},
            "B": {"good": 0, "bad": 0},
        }
        for e in entries:
            if e.ab_variant in counts:
                counts[e.ab_variant][e.rating] += 1

        summary: dict[str, Any] = {}
        for variant in ("A", "B"):
            total = counts[variant]["good"] + counts[variant]["bad"]
            summary[variant] = {
                "good": counts[variant]["good"],
                "bad": counts[variant]["bad"],
                "total": total,
                "good_rate": (
                    round(counts[variant]["good"] / total, 4) if total > 0 else None
                ),
            }

        summary["statistical_test"] = _two_proportion_z_test(
            good_a=counts["A"]["good"],
            total_a=summary["A"]["total"],
            good_b=counts["B"]["good"],
            total_b=summary["B"]["total"],
        )
        return summary
