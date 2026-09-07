"""
Unit Tests for Closed-Loop Execution Feedback & Buffer Calibration.
"""

import pytest
from app.services.execution.feedback_engine import ExecutionFeedbackEngine, ClosedLoopMetrics


@pytest.fixture
def engine():
    return ExecutionFeedbackEngine()


def test_analyze_execution_feedback_returns_metrics(engine):
    metrics = engine.analyze_execution_feedback()
    assert isinstance(metrics, ClosedLoopMetrics)
    assert 0.0 <= metrics.completion_rate_pct <= 100.0
    assert 0.0 <= metrics.overrun_rate_pct <= 100.0
    assert 0.0 <= metrics.reschedule_acceptance_rate_pct <= 100.0
    assert metrics.feedback_timestamp != ""


def test_get_section_duration_modifier(engine):
    modifier = engine.get_section_duration_modifier("SEC_001")
    assert isinstance(modifier, float)
    assert modifier >= 0.0
