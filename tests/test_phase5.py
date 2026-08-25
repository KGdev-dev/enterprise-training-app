"""Tests for Phase 5 end-to-end integration flow."""

from __future__ import annotations

from src.bugzot import BugzotMonitor
from src.engine import RegistrationEngine
from src.models import Assessment, Course, Learner
from src.patterns import AppConfig, StandardPercentageStrategy


def test_end_to_end_registration_lifecycle() -> None:
    AppConfig.reset_instance()
    config = AppConfig.get_instance(environment="test")
    monitor = BugzotMonitor.get_instance()
    monitor.events.clear()
    monitor.metrics = {
        "total_processed": 0,
        "success": 0,
        "rejected": 0,
        "total_time_ms": 0,
    }

    learners = {
        "L1": Learner("L1", "Alice", "alice@example.com"),
        "L2": Learner("L2", "Bob", "bob@example.com"),
        "L3": Learner("L3", "Cara", "cara@example.com"),
    }
    courses = {"C1": Course("C1", "Enterprise Python", capacity=2)}
    engine = RegistrationEngine(courses=courses, learners=learners, monitor=monitor)

    summary = engine.process_batch(
        [
            {"registration_id": "R1", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R2", "learner_id": "L2", "course_id": "C1"},
            {"registration_id": "R3", "learner_id": "L3", "course_id": "C1"},
        ]
    )

    assert config.environment == "test"
    assert summary["successful_count"] == 2
    assert summary["rejected_count"] == 1
    assert summary["rejection_reasons"] == {"Capacity Exceeded": 1}
    assert any("Capacity exceeded" in event["message"] for event in monitor.events)

    assessment = Assessment(
        assessment_id="A1",
        learner_id="L1",
        course_id="C1",
        raw_score=45,
        max_score=50,
        grading_strategy=StandardPercentageStrategy(),
    )
    result = assessment.calculate_result()

    assert courses["C1"].enrolled_count == 2
    assert result["passed"] is True
