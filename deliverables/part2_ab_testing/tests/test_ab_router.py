"""Unit tests for the A/B traffic-split router.

All tests use the optional pct/salt keyword arguments on assign_variant so that
the module-level ab_settings singleton does not need to be mocked.
"""

import logging
from unittest.mock import MagicMock

from deliverables.part2_ab_testing.ab_router import (
    assign_variant,
    get_graph_for_variant,
    log_assignment,
)


class TestAssignVariant:
    def test_determinism(self) -> None:
        """Same inputs must always return the same variant."""
        results = {assign_variant("user_001", pct=50) for _ in range(100)}
        assert len(results) == 1

    def test_all_traffic_to_a(self) -> None:
        user_ids = [f"user_{i:06d}" for i in range(200)]
        variants = [assign_variant(uid, pct=0) for uid in user_ids]
        assert all(v == "A" for v in variants)

    def test_all_traffic_to_b(self) -> None:
        user_ids = [f"user_{i:06d}" for i in range(200)]
        variants = [assign_variant(uid, pct=100) for uid in user_ids]
        assert all(v == "B" for v in variants)

    def test_distribution_near_50_50(self) -> None:
        """With 10 000 users the B-rate should fall within ±2 pp of 50%."""
        user_ids = [f"user_{i:06d}" for i in range(10_000)]
        b_count = sum(1 for uid in user_ids if assign_variant(uid, pct=50) == "B")
        assert abs(b_count / 10_000 - 0.50) < 0.02

    def test_distribution_near_30_pct(self) -> None:
        """With 10 000 users the B-rate should fall within ±2 pp of 30%."""
        user_ids = [f"user_{i:06d}" for i in range(10_000)]
        b_count = sum(1 for uid in user_ids if assign_variant(uid, pct=30) == "B")
        assert abs(b_count / 10_000 - 0.30) < 0.02

    def test_salt_isolation(self) -> None:
        """Different salts must reassign a meaningful fraction of users."""
        user_ids = [f"user_{i:06d}" for i in range(1_000)]
        results_s1 = [assign_variant(uid, pct=50, salt="salt-one") for uid in user_ids]
        results_s2 = [assign_variant(uid, pct=50, salt="salt-two") for uid in user_ids]
        flipped = sum(1 for a, b in zip(results_s1, results_s2) if a != b)
        # At least 10% of users should switch variant when the salt changes.
        assert flipped > 100

    def test_returns_literal_a_or_b(self) -> None:
        for uid in [f"user_{i:03d}" for i in range(1, 9)]:
            assert assign_variant(uid) in ("A", "B")


class TestGetGraphForVariant:
    def test_returns_graph_a(self) -> None:
        mock_state = MagicMock()
        graph = get_graph_for_variant("A", mock_state)
        assert graph is mock_state.graph_a

    def test_returns_graph_b(self) -> None:
        mock_state = MagicMock()
        graph = get_graph_for_variant("B", mock_state)
        assert graph is mock_state.graph_b


class TestLogAssignment:
    def test_logs_variant_and_user(self) -> None:
        mock_logger = MagicMock(spec=logging.Logger)
        log_assignment("user_001", "B", "corr-xyz", mock_logger)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        # The format string and positional args contain the relevant values.
        log_str = call_args[0][0] % call_args[0][1:]
        assert "B" in log_str
        assert "user_001" in log_str
        assert "corr-xyz" in log_str
