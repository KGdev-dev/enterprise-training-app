"""Enterprise design pattern implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Lock
from typing import Any
from uuid import uuid4

from src.models import SupportTicket, TicketPriority


class AppConfig:
    """Thread-safe singleton for application configuration."""

    _instance: AppConfig | None = None
    _lock: Lock = Lock()

    def __init__(
        self,
        environment: str = "development",
        max_concurrent_registrations: int = 50,
        db_url: str = "sqlite:///enterprise_training.db",
        default_page_size: int = 25,
    ) -> None:
        if not environment.strip():
            raise ValueError("environment must not be empty")
        if max_concurrent_registrations <= 0:
            raise ValueError("max_concurrent_registrations must be positive")
        if not db_url.strip():
            raise ValueError("db_url must not be empty")
        if default_page_size <= 0:
            raise ValueError("default_page_size must be positive")

        self.environment = environment
        self.max_concurrent_registrations = max_concurrent_registrations
        self.db_url = db_url
        self.default_page_size = default_page_size

    @classmethod
    def get_instance(cls, **kwargs: Any) -> AppConfig:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            cls._instance = None


class AssessmentStrategy(ABC):
    """Strategy interface used by assessments."""

    @abstractmethod
    def calculate(self, raw_score: float, max_score: float) -> dict[str, Any]:
        """Calculate an assessment outcome."""


@dataclass(frozen=True)
class StandardPercentageStrategy(AssessmentStrategy):
    """Returns percentage, pass/fail, and letter grade."""

    pass_threshold: float = 50.0

    def calculate(self, raw_score: float, max_score: float) -> dict[str, Any]:
        percentage = (raw_score / max_score) * 100
        if percentage >= 85:
            letter_grade = "A"
        elif percentage >= 70:
            letter_grade = "B"
        elif percentage >= self.pass_threshold:
            letter_grade = "C"
        else:
            letter_grade = "F"

        return {
            "percentage": round(percentage, 2),
            "passed": percentage >= self.pass_threshold,
            "letter_grade": letter_grade,
        }


@dataclass(frozen=True)
class PassFailCompetencyStrategy(AssessmentStrategy):
    """Returns a competency-focused evaluation."""

    competency_threshold: float = 80.0

    def calculate(self, raw_score: float, max_score: float) -> dict[str, Any]:
        percentage = (raw_score / max_score) * 100
        return {
            "percentage": round(percentage, 2),
            "competent": percentage >= self.competency_threshold,
        }


@dataclass(frozen=True)
class WeightedAssessmentStrategy(AssessmentStrategy):
    """Applies a configurable weighting multiplier to percentage score."""

    weight: float = 1.0
    pass_threshold: float = 50.0

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight must be positive")
        if self.pass_threshold < 0:
            raise ValueError("pass_threshold cannot be negative")

    def calculate(self, raw_score: float, max_score: float) -> dict[str, Any]:
        percentage = (raw_score / max_score) * 100
        weighted_percentage = percentage * self.weight
        return {
            "percentage": round(percentage, 2),
            "weighted_percentage": round(weighted_percentage, 2),
            "passed": weighted_percentage >= self.pass_threshold,
        }


@dataclass
class TechnicalSupportTicket(SupportTicket):
    """Technical support ticket with routing metadata."""

    routing_tag: str = "TECH"


@dataclass
class BillingSupportTicket(SupportTicket):
    """Billing support ticket with routing metadata."""

    routing_tag: str = "BILLING"


@dataclass
class CourseInquiryTicket(SupportTicket):
    """Course inquiry ticket with routing metadata."""

    routing_tag: str = "COURSE"


class SupportTicketFactory:
    """Factory for creating specialized support tickets."""

    @staticmethod
    def create_ticket(
        ticket_type: str,
        learner_id: str,
        description: str,
        **kwargs: Any,
    ) -> SupportTicket:
        if not ticket_type.strip():
            raise ValueError("ticket_type must not be empty")

        normalized_type = ticket_type.strip().lower()
        ticket_id = kwargs.pop("ticket_id", str(uuid4()))
        created_at = kwargs.pop("created_at", None)
        status = kwargs.pop("status", None)

        base_kwargs: dict[str, Any] = {
            "ticket_id": ticket_id,
            "learner_id": learner_id,
            "issue_description": description,
        }
        if created_at is not None:
            base_kwargs["created_at"] = created_at
        if status is not None:
            base_kwargs["status"] = status

        if normalized_type in {"technical", "tech"}:
            base_kwargs["priority"] = kwargs.pop("priority", TicketPriority.HIGH)
            return TechnicalSupportTicket(**base_kwargs)
        if normalized_type in {"billing", "bill"}:
            base_kwargs["priority"] = kwargs.pop("priority", TicketPriority.MEDIUM)
            return BillingSupportTicket(**base_kwargs)
        if normalized_type in {"course_inquiry", "inquiry", "course"}:
            base_kwargs["priority"] = kwargs.pop("priority", TicketPriority.LOW)
            return CourseInquiryTicket(**base_kwargs)

        raise ValueError(f"Unsupported ticket_type: {ticket_type}")
