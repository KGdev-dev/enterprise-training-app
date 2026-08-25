"""Tests for Phase 3 Bugzot monitoring and optimization."""

from __future__ import annotations

from src.bugzot import BugzotMonitor
from src.engine import RegistrationEngine, compare_optimization_benchmark
from src.models import Course, Learner, RegistrationStatus


def test_bugzot_event_logging_and_filtering() -> None:
    BugzotMonitor.reset_instance()
    monitor = BugzotMonitor.get_instance()

    monitor.log_event("INFO", "lifecycle", "Engine started", {"component": "registration"})
    monitor.log_duplicate_attempt("L1", "C1")
    monitor.log_capacity_violation("C1", 2)
    monitor.log_validation_failure("learner_email", "bad-email", "malformed learner email")

    warning_events = monitor.get_events(level="WARNING")
    assert len(warning_events) == 3
    duplicate_events = monitor.get_events(category="duplicate_registration")
    assert len(duplicate_events) == 1
    assert duplicate_events[0]["payload"]["learner_id"] == "L1"


def test_bugzot_report_calculates_latency_and_outcomes() -> None:
    BugzotMonitor.reset_instance()
    monitor = BugzotMonitor.get_instance()

    for latency in (10.0, 20.0, 30.0):
        monitor.increment_attempted()
        monitor.record_latency_ms(latency)
    monitor.mark_transaction_outcome(RegistrationStatus.CONFIRMED)
    monitor.mark_transaction_outcome(RegistrationStatus.REJECTED)
    monitor.mark_transaction_outcome(RegistrationStatus.FAILED)
    monitor.log_capacity_violation("C1", 1)
    monitor.log_duplicate_attempt("L1", "C1")
    monitor.log_capacity_violation("C1", 1)

    report = monitor.generate_performance_report()
    counters = report["transaction_counters"]
    latency = report["latency_ms"]

    assert counters == {
        "total_attempted": 3,
        "total_confirmed": 1,
        "total_rejected": 2,
    }
    assert latency["average"] == 20.0
    assert latency["min"] == 10.0
    assert latency["max"] == 30.0
    assert report["success_rate"] == 1 / 3
    assert report["failure_rate"] == 2 / 3
    assert report["top_error_categories"][0] == ("capacity_violation", 2)


def test_engine_integration_populates_bugzot_metrics_and_events() -> None:
    BugzotMonitor.reset_instance()
    monitor = BugzotMonitor.get_instance()
    course = Course("C1", "Scalable Python", 1)
    learners = [
        Learner("L1", "Learner One", "one@example.com"),
        Learner("L2", "Learner Two", "two@example.com"),
    ]
    engine = RegistrationEngine(courses=[course], learners=learners, monitor=monitor)

    summary = engine.process_concurrently(
        [
            {"registration_id": "R1", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R2", "learner_id": "L1", "course_id": "C1"},
            {"registration_id": "R3", "learner_id": "L2", "course_id": "C1"},
        ],
        max_workers=3,
    )
    report = monitor.generate_performance_report()

    assert summary["successful_count"] == 1
    assert summary["rejected_count"] == 2
    assert report["transaction_counters"]["total_attempted"] == 3
    assert report["transaction_counters"]["total_confirmed"] == 1
    assert report["transaction_counters"]["total_rejected"] == 2
    assert len(monitor.get_events(category="duplicate_registration")) == 1
    assert len(monitor.get_events(category="capacity_violation")) == 1


def test_optimized_benchmark_is_faster_than_unoptimized() -> None:
    benchmark = compare_optimization_benchmark(1000)

    assert benchmark["optimized_seconds"] < benchmark["unoptimized_seconds"]
    assert benchmark["speedup_factor"] > 1.0
