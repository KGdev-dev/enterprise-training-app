"""Tests for Phase 2 registration processing engine."""

from __future__ import annotations

from src.engine import RegistrationEngine
from src.models import Course, Learner, RegistrationStatus


def _build_engine(course_capacity: int = 3) -> tuple[RegistrationEngine, list[Course], list[Learner]]:
    courses = [
        Course("C1", "Python Concurrency", course_capacity),
        Course("C2", "Inactive Course", 5, active_status=False),
    ]
    learners = [
        Learner("L1", "Alice", "alice@example.com"),
        Learner("L2", "Bob", "bob@example.com"),
        Learner("L3", "Cara", "cara@example.com"),
        Learner("L4", "Drew", "drew@example.com"),
    ]
    return RegistrationEngine(courses, learners), courses, learners


def test_process_batch_enforces_basic_business_rules() -> None:
    engine, _, _ = _build_engine(course_capacity=3)

    summary = engine.process_batch(
        [
            {"registration_id": "R1", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R2", "learner_id": "L2", "course_id": "C2"},
            {"registration_id": "R3", "learner_id": "L9", "course_id": "C1"},
            {"registration_id": "R4", "learner_id": "L3", "course_id": "C9"},
        ]
    )

    assert summary["total_processed"] == 4
    assert summary["successful_count"] == 1
    assert summary["rejected_count"] == 3
    assert summary["rejection_reasons"] == {
        "Inactive Course": 1,
        "Invalid Learner": 1,
        "Invalid Course": 1,
    }


def test_duplicate_prevention_rejects_second_attempt() -> None:
    engine, courses, _ = _build_engine(course_capacity=2)

    summary = engine.process_batch(
        [
            {"registration_id": "R1", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R2", "learner_id": "L1", "course_id": "C1"},
        ]
    )

    assert summary["successful_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["rejection_reasons"]["Duplicate Registration"] == 1
    assert courses[0].enrolled_count == 1


def test_capacity_boundary_rejects_third_registration() -> None:
    engine, courses, _ = _build_engine(course_capacity=2)

    summary = engine.process_batch(
        [
            {"registration_id": "R1", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R2", "learner_id": "L2", "course_id": "C1"},
            {"registration_id": "R3", "learner_id": "L3", "course_id": "C1"},
        ]
    )

    assert summary["successful_count"] == 2
    assert summary["rejected_count"] == 1
    assert summary["rejection_reasons"]["Capacity Exceeded"] == 1
    assert courses[0].enrolled_count == 2


def test_concurrent_stress_limits_to_capacity_without_race_conditions() -> None:
    course = Course("C-STRESS", "Stress Course", 5)
    learners = [
        Learner(f"L{index}", f"Learner {index}", f"learner{index}@example.com")
        for index in range(20)
    ]
    engine = RegistrationEngine(courses=[course], learners=learners)

    requests = [
        {
            "registration_id": f"R{index}",
            "learner_id": f"L{index}",
            "course_id": "C-STRESS",
        }
        for index in range(20)
    ]

    summary = engine.process_concurrently(requests, max_workers=20)

    assert summary["total_processed"] == 20
    assert summary["successful_count"] == 5
    assert summary["rejected_count"] == 15
    assert summary["rejection_reasons"] == {"Capacity Exceeded": 15}
    assert course.enrolled_count == 5

    confirmed = [
        result
        for result in summary["results"]
        if result["status"] is RegistrationStatus.CONFIRMED
    ]
    assert len(confirmed) == 5
