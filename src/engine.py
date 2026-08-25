"""Registration processing engine with sequential and concurrent execution."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock, get_ident
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4

from src.bugzot import BugzotMonitor
from src.models import Course, Learner, Registration, RegistrationStatus


@dataclass(frozen=True)
class ProcessingReason:
    """Standardized processing reason labels."""

    INVALID_REQUEST: str = "Invalid Request"
    INVALID_LEARNER: str = "Invalid Learner"
    INVALID_COURSE: str = "Invalid Course"
    INACTIVE_COURSE: str = "Inactive Course"
    DUPLICATE: str = "Duplicate Registration"
    CAPACITY_EXCEEDED: str = "Capacity Exceeded"
    UNHANDLED_EXCEPTION: str = "Unhandled Exception"
    SUCCESS: str = "Success"


class RegistrationEngine:
    """Processes learner course registration requests with integrity guarantees."""

    def __init__(
        self,
        courses: list[Course],
        learners: list[Learner],
        monitor: BugzotMonitor | None = None,
    ) -> None:
        self._courses: dict[str, Course] = {course.course_id: course for course in courses}
        self._learners: dict[str, Learner] = {
            learner.learner_id: learner for learner in learners
        }
        self._monitor = monitor or BugzotMonitor.get_instance()
        self._registration_pairs: set[tuple[str, str]] = set()
        self._registrations: list[Registration] = []
        self._processing_summaries: list[dict[str, Any]] = []

        self._pair_lock = Lock()
        self._summary_lock = Lock()
        self._course_locks: dict[str, Lock] = {
            course_id: Lock() for course_id in self._courses
        }

    @property
    def registrations(self) -> list[Registration]:
        return list(self._registrations)

    @property
    def processing_summaries(self) -> list[dict[str, Any]]:
        return list(self._processing_summaries)

    def process_batch(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        results = [self._process_single_request(request) for request in requests]
        return self._build_summary(results)

    def process_concurrently(
        self, registration_requests: list[dict[str, Any]], max_workers: int = 4
    ) -> dict[str, Any]:
        start = perf_counter()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self._process_single_request, registration_requests))
        summary = self._build_summary(results)
        summary["execution_time_seconds"] = perf_counter() - start
        return summary

    def _process_single_request(self, request: dict[str, Any]) -> dict[str, Any]:
        reason = ProcessingReason()
        start = perf_counter()
        self._monitor.increment_attempted()
        learner_id = str(request.get("learner_id", "")).strip()
        course_id = str(request.get("course_id", "")).strip()
        registration_id = str(
            request.get("registration_id")
            or f"R-{uuid4().hex[:10].upper()}"
        )
        thread_id = get_ident()
        malformed_email = str(request.get("learner_email", "")).strip()

        try:
            if malformed_email and ("@" not in malformed_email or "." not in malformed_email):
                self._monitor.log_validation_failure(
                    "learner_email",
                    malformed_email,
                    "malformed learner email",
                )
                result = {
                    "thread_id": thread_id,
                    "registration": None,
                    "status": RegistrationStatus.FAILED,
                    "reason": reason.INVALID_REQUEST,
                }
                self._record_result(result)
                return result

            if not learner_id or not course_id:
                self._monitor.log_validation_failure(
                    "registration_request",
                    f"{learner_id}:{course_id}",
                    "missing learner_id or course_id",
                )
                result = {
                    "thread_id": thread_id,
                    "registration": None,
                    "status": RegistrationStatus.FAILED,
                    "reason": reason.INVALID_REQUEST,
                }
                self._record_result(result)
                return result

            learner = self._learners.get(learner_id)
            if learner is None:
                self._monitor.log_validation_failure(
                    "learner_id", learner_id, "unknown learner"
                )
                result = {
                    "thread_id": thread_id,
                    "registration": None,
                    "status": RegistrationStatus.REJECTED,
                    "reason": reason.INVALID_LEARNER,
                }
                self._record_result(result)
                return result

            course = self._courses.get(course_id)
            if course is None:
                self._monitor.log_validation_failure("course_id", course_id, "unknown course")
                result = {
                    "thread_id": thread_id,
                    "registration": None,
                    "status": RegistrationStatus.REJECTED,
                    "reason": reason.INVALID_COURSE,
                }
                self._record_result(result)
                return result

            registration = Registration(registration_id, learner, course)
            pair = (learner_id, course_id)
            course_lock = self._course_locks[course_id]

            with self._monitored_lock(
                self._pair_lock,
                lock_name="pair_lock",
                payload={"learner_id": learner_id, "course_id": course_id},
            ):
                if pair in self._registration_pairs:
                    registration.status = RegistrationStatus.REJECTED
                    self._monitor.log_duplicate_attempt(learner_id, course_id)
                    result = {
                        "thread_id": thread_id,
                        "registration": registration,
                        "status": registration.status,
                        "reason": reason.DUPLICATE,
                    }
                    self._record_result(result)
                    return result

                with self._monitored_lock(
                    course_lock,
                    lock_name=f"course_lock:{course_id}",
                    payload={"learner_id": learner_id, "course_id": course_id},
                ):
                    if not course.active_status:
                        registration.status = RegistrationStatus.REJECTED
                        result = {
                            "thread_id": thread_id,
                            "registration": registration,
                            "status": registration.status,
                            "reason": reason.INACTIVE_COURSE,
                        }
                        self._record_result(result)
                        return result

                    if not course.has_available_slot():
                        registration.status = RegistrationStatus.REJECTED
                        self._monitor.log_capacity_violation(course_id, course.capacity)
                        result = {
                            "thread_id": thread_id,
                            "registration": registration,
                            "status": registration.status,
                            "reason": reason.CAPACITY_EXCEEDED,
                        }
                        self._record_result(result)
                        return result

                    course.increment_enrolment()
                    learner.add_course(course)
                    self._registration_pairs.add(pair)
                    registration.status = RegistrationStatus.CONFIRMED

            result = {
                "thread_id": thread_id,
                "registration": registration,
                "status": registration.status,
                "reason": reason.SUCCESS,
            }
            self._record_result(result)
            return result
        except Exception as error:
            self._monitor.log_unhandled_exception(
                "process_registration_request",
                error,
                payload={"thread_id": thread_id, "learner_id": learner_id, "course_id": course_id},
            )
            result = {
                "thread_id": thread_id,
                "registration": None,
                "status": RegistrationStatus.FAILED,
                "reason": reason.UNHANDLED_EXCEPTION,
            }
            self._record_result(result)
            return result
        finally:
            self._monitor.record_latency_ms((perf_counter() - start) * 1000)

    def _record_result(self, result: dict[str, Any]) -> None:
        with self._summary_lock:
            self._processing_summaries.append(result)
            registration = result.get("registration")
            if registration is not None:
                self._registrations.append(registration)
            self._monitor.mark_transaction_outcome(result["status"])

    @contextmanager
    def _monitored_lock(
        self,
        lock: Lock,
        *,
        lock_name: str,
        payload: dict[str, Any],
    ) -> Iterator[None]:
        if lock.acquire(blocking=False):
            try:
                yield
            finally:
                lock.release()
            return

        wait_start = perf_counter()
        lock.acquire()
        wait_ms = (perf_counter() - wait_start) * 1000
        self._monitor.log_lock_wait(lock_name, wait_ms, payload=payload)
        try:
            yield
        finally:
            lock.release()

    def _build_summary(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        success_count = sum(
            1 for result in results if result["status"] is RegistrationStatus.CONFIRMED
        )
        rejected_results = [
            result
            for result in results
            if result["status"] is not RegistrationStatus.CONFIRMED
        ]
        reasons = Counter(result["reason"] for result in rejected_results)

        return {
            "total_processed": len(results),
            "successful_count": success_count,
            "rejected_count": len(rejected_results),
            "rejection_reasons": dict(reasons),
            "registrations": [
                result["registration"]
                for result in results
                if result["registration"] is not None
            ],
            "results": results,
        }


def compare_optimization_benchmark(total_requests: int = 1000) -> dict[str, float]:
    """Compares unoptimized O(N) duplicate checks with optimized O(1) batched checks."""

    requests = [
        {
            "learner_id": f"L-{index % 400:04d}",
            "course_id": f"C-{index % 5:03d}",
        }
        for index in range(total_requests)
    ]

    unoptimized_history: list[tuple[str, str]] = []
    unoptimized_lock = Lock()
    unoptimized_start = perf_counter()
    for request in requests:
        pair = (request["learner_id"], request["course_id"])
        with unoptimized_lock:
            is_duplicate = False
            for existing_pair in unoptimized_history:
                if existing_pair == pair:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unoptimized_history.append(pair)
    unoptimized_elapsed = perf_counter() - unoptimized_start

    optimized_history: set[tuple[str, str]] = set()
    optimized_lock = Lock()
    batch_size = 40
    optimized_start = perf_counter()
    for batch_start in range(0, len(requests), batch_size):
        batch = requests[batch_start : batch_start + batch_size]
        with optimized_lock:
            for request in batch:
                pair = (request["learner_id"], request["course_id"])
                if pair not in optimized_history:
                    optimized_history.add(pair)
    optimized_elapsed = perf_counter() - optimized_start

    speedup = (
        unoptimized_elapsed / optimized_elapsed
        if optimized_elapsed > 0
        else float("inf")
    )
    return {
        "total_requests": float(total_requests),
        "unoptimized_seconds": unoptimized_elapsed,
        "optimized_seconds": optimized_elapsed,
        "speedup_factor": speedup,
    }
