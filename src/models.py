"""Domain models for enterprise training app."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.patterns import AssessmentStrategy

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class RegistrationStatus(str, Enum):
    """Lifecycle statuses for learner registrations."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TicketPriority(str, Enum):
    """Priority levels for support tickets."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TicketStatus(str, Enum):
    """Lifecycle statuses for support tickets."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


@dataclass
class Course:
    """Represents a course available for registration."""

    course_id: str
    title: str
    capacity: int
    active_status: bool = True
    enrolled_count: int = 0

    def __post_init__(self) -> None:
        if not self.course_id.strip():
            raise ValueError("course_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if self.capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if self.enrolled_count < 0:
            raise ValueError("enrolled_count cannot be negative")
        if self.enrolled_count > self.capacity:
            raise ValueError("enrolled_count cannot exceed capacity")

    def has_available_slot(self) -> bool:
        return self.active_status and self.enrolled_count < self.capacity

    def increment_enrolment(self) -> None:
        if not self.has_available_slot():
            raise ValueError("No available slots for this course")
        self.enrolled_count += 1


@dataclass
class Learner:
    """Represents a platform learner."""

    learner_id: str
    name: str
    email: str
    registered_courses: list[Course] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not self.email.strip():
            raise ValueError("email must not be empty")
        if not _EMAIL_RE.match(self.email):
            raise ValueError("email must be valid")

    def add_course(self, course: Course) -> None:
        if course in self.registered_courses:
            return
        self.registered_courses.append(course)


@dataclass
class Registration:
    """Represents learner registration in a specific course."""

    registration_id: str
    learner: Learner
    course: Course
    registration_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: RegistrationStatus = RegistrationStatus.PENDING

    def __post_init__(self) -> None:
        if not self.registration_id.strip():
            raise ValueError("registration_id must not be empty")


@dataclass
class Assessment:
    """Represents an assessment result to be evaluated by a strategy."""

    assessment_id: str
    learner_id: str
    course_id: str
    raw_score: float
    max_score: float
    grading_strategy: "AssessmentStrategy"

    def __post_init__(self) -> None:
        if not self.assessment_id.strip():
            raise ValueError("assessment_id must not be empty")
        if not self.learner_id.strip():
            raise ValueError("learner_id must not be empty")
        if not self.course_id.strip():
            raise ValueError("course_id must not be empty")
        if self.raw_score < 0:
            raise ValueError("raw_score cannot be negative")
        if self.max_score <= 0:
            raise ValueError("max_score must be positive")
        if self.raw_score > self.max_score:
            raise ValueError("raw_score cannot exceed max_score")

    def calculate_result(self) -> dict[str, Any]:
        return self.grading_strategy.calculate(self.raw_score, self.max_score)


@dataclass
class SupportTicket:
    """Base support ticket model used by specific ticket types."""

    ticket_id: str
    learner_id: str
    issue_description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.ticket_id.strip():
            raise ValueError("ticket_id must not be empty")
        if not self.learner_id.strip():
            raise ValueError("learner_id must not be empty")
        if not self.issue_description.strip():
            raise ValueError("issue_description must not be empty")
