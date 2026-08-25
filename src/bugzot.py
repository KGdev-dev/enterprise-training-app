"""Bugzot monitoring subsystem for diagnostics and performance tracking."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from threading import Lock
from time import perf_counter
from typing import Any, Callable, Iterator

from src.models import RegistrationStatus

LogLevel = str


class BugzotMonitor:
    """Thread-safe singleton monitor for events and registration metrics."""

    _instance: "BugzotMonitor | None" = None
    _instance_lock = Lock()

    def __init__(self) -> None:
        self._lock = Lock()
        self._events: list[dict[str, Any]] = []
        self._latencies_ms: list[float] = []
        self._counters = Counter(
            {
                "total_attempted": 0,
                "total_confirmed": 0,
                "total_rejected": 0,
            }
        )
        self._error_categories: Counter[str] = Counter()

    @classmethod
    def get_instance(cls) -> "BugzotMonitor":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None

    def log_event(
        self,
        level: LogLevel,
        category: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "category": category,
            "message": message,
            "payload": payload or {},
        }
        with self._lock:
            self._events.append(event)
            if level in {"WARNING", "ERROR"}:
                self._error_categories[category] += 1

    def log_validation_failure(
        self,
        field_name: str,
        field_value: str,
        reason: str,
    ) -> None:
        self.log_event(
            "WARNING",
            "validation_failure",
            "Validation failed for registration request",
            {
                "field": field_name,
                "value": field_value,
                "reason": reason,
            },
        )

    def log_duplicate_attempt(self, learner_id: str, course_id: str) -> None:
        self.log_event(
            "WARNING",
            "duplicate_registration",
            "Duplicate registration attempt blocked",
            {"learner_id": learner_id, "course_id": course_id},
        )

    def log_capacity_violation(self, course_id: str, capacity: int) -> None:
        self.log_event(
            "WARNING",
            "capacity_violation",
            "Course capacity exceeded",
            {"course_id": course_id, "capacity": capacity},
        )

    def log_lock_wait(
        self,
        lock_name: str,
        wait_ms: float,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.log_event(
            "INFO",
            "concurrency_lock_wait",
            "Thread waited to acquire lock",
            {"lock_name": lock_name, "wait_ms": wait_ms, **(payload or {})},
        )

    def log_unhandled_exception(
        self,
        operation: str,
        error: Exception,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.log_event(
            "ERROR",
            "unhandled_exception",
            "Unhandled exception during registration processing",
            {
                "operation": operation,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **(payload or {}),
            },
        )

    def increment_attempted(self) -> None:
        with self._lock:
            self._counters["total_attempted"] += 1

    def record_latency_ms(self, latency_ms: float) -> None:
        with self._lock:
            self._latencies_ms.append(latency_ms)

    def mark_transaction_outcome(self, status: RegistrationStatus) -> None:
        with self._lock:
            if status is RegistrationStatus.CONFIRMED:
                self._counters["total_confirmed"] += 1
            else:
                self._counters["total_rejected"] += 1

    def get_events(
        self,
        *,
        level: LogLevel | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._events)
        if level is not None:
            events = [event for event in events if event["level"] == level]
        if category is not None:
            events = [event for event in events if event["category"] == category]
        return events

    def generate_performance_report(self) -> dict[str, Any]:
        with self._lock:
            attempted = self._counters["total_attempted"]
            confirmed = self._counters["total_confirmed"]
            rejected = self._counters["total_rejected"]
            latencies = list(self._latencies_ms)
            top_errors = self._error_categories.most_common(5)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        min_latency = min(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        total_duration_seconds = sum(latencies) / 1000 if latencies else 0.0
        throughput = confirmed / total_duration_seconds if total_duration_seconds else 0.0
        success_rate = (confirmed / attempted) if attempted else 0.0
        failure_rate = (rejected / attempted) if attempted else 0.0

        return {
            "transaction_counters": {
                "total_attempted": attempted,
                "total_confirmed": confirmed,
                "total_rejected": rejected,
            },
            "throughput_tps": throughput,
            "latency_ms": {
                "average": avg_latency,
                "min": min_latency,
                "max": max_latency,
            },
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "top_error_categories": top_errors,
        }

    def print_formatted_report(self) -> None:
        report = self.generate_performance_report()
        counters = report["transaction_counters"]
        latency = report["latency_ms"]
        print("\n[Bugzot Performance & Operational Metrics]")
        print(f"Attempted: {counters['total_attempted']}")
        print(f"Confirmed: {counters['total_confirmed']}")
        print(f"Rejected: {counters['total_rejected']}")
        print(f"Throughput (txn/s): {report['throughput_tps']:.2f}")
        print(
            "Latency (ms): "
            f"avg={latency['average']:.3f}, min={latency['min']:.3f}, max={latency['max']:.3f}"
        )
        print(
            f"Success rate: {report['success_rate']:.2%} | "
            f"Failure rate: {report['failure_rate']:.2%}"
        )
        if report["top_error_categories"]:
            print("Top Error Categories:")
            for category, count in report["top_error_categories"]:
                print(f"  - {category}: {count}")
        else:
            print("Top Error Categories: none")


@contextmanager
def bugzot_timer(operation_name: str, monitor: BugzotMonitor | None = None) -> Iterator[None]:
    """Context manager for operation-level duration tracking."""

    active_monitor = monitor or BugzotMonitor.get_instance()
    start = perf_counter()
    try:
        yield
    finally:
        duration_ms = (perf_counter() - start) * 1000
        active_monitor.record_latency_ms(duration_ms)
        active_monitor.log_event(
            "INFO",
            "performance_trace",
            "Operation execution traced",
            {"operation_name": operation_name, "duration_ms": duration_ms},
        )


def bugzot_trace(operation_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for operation-level duration tracking."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with bugzot_timer(operation_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
