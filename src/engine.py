"""Registration processing engine with sequential and concurrent execution."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock, get_ident
from time import perf_counter
from typing import Any
from uuid import uuid4

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
    SUCCESS: str = "Success"


class RegistrationEngine:
    """Processes learner course registration requests with integrity guarantees."""

    def __init__(self, courses: list[Course], learners: list[Learner]) -> None:
        self._courses: dict[str, Course] = {course.course_id: course for course in courses}
        self._learners: dict[str, Learner] = {
            learner.learner_id: learner for learner in learners
        }
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
        learner_id = str(request.get("learner_id", "")).strip()
        course_id = str(request.get("course_id", "")).strip()
        registration_id = str(
            request.get("registration_id")
            or f"R-{uuid4().hex[:10].upper()}"
        )
        thread_id = get_ident()

        if not learner_id or not course_id:
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

        with self._pair_lock:
            if pair in self._registration_pairs:
                registration.status = RegistrationStatus.REJECTED
                result = {
                    "thread_id": thread_id,
                    "registration": registration,
                    "status": registration.status,
                    "reason": reason.DUPLICATE,
                }
                self._record_result(result)
                return result

            with course_lock:
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

    def _record_result(self, result: dict[str, Any]) -> None:
        with self._summary_lock:
            self._processing_summaries.append(result)
            registration = result.get("registration")
            if registration is not None:
                self._registrations.append(registration)

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
