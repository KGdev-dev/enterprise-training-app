"""Tests for Phase 1 models and design patterns."""

from __future__ import annotations

import pytest

from src.models import (
    Assessment,
    Course,
    Learner,
    Registration,
    RegistrationStatus,
    TicketPriority,
)
from src.patterns import (
    AppConfig,
    BillingSupportTicket,
    CourseInquiryTicket,
    PassFailCompetencyStrategy,
    StandardPercentageStrategy,
    SupportTicketFactory,
    TechnicalSupportTicket,
    WeightedAssessmentStrategy,
)


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    AppConfig.reset_instance()


def test_learner_creation_and_course_relationship() -> None:
    learner = Learner("L1", "Alice", "alice@example.com")
    course = Course("C1", "Python", 2)

    learner.add_course(course)
    learner.add_course(course)

    assert learner.registered_courses == [course]


def test_learner_invalid_email_raises_error() -> None:
    with pytest.raises(ValueError, match="email must be valid"):
        Learner("L1", "Alice", "invalid-email")


def test_course_capacity_validation_and_enrolment() -> None:
    with pytest.raises(ValueError, match="capacity must be a positive integer"):
        Course("C1", "Python", 0)

    course = Course("C1", "Python", 1)
    assert course.has_available_slot() is True

    course.increment_enrolment()

    assert course.enrolled_count == 1
    assert course.has_available_slot() is False
    with pytest.raises(ValueError, match="No available slots"):
        course.increment_enrolment()


def test_registration_creation_defaults() -> None:
    learner = Learner("L1", "Alice", "alice@example.com")
    course = Course("C1", "Python", 3)

    registration = Registration("R1", learner, course)

    assert registration.status is RegistrationStatus.PENDING
    assert registration.learner is learner
    assert registration.course is course


def test_assessment_validation_and_calculation() -> None:
    strategy = StandardPercentageStrategy()
    assessment = Assessment(
        "A1",
        learner_id="L1",
        course_id="C1",
        raw_score=45,
        max_score=50,
        grading_strategy=strategy,
    )

    result = assessment.calculate_result()

    assert result["percentage"] == 90.0
    assert result["passed"] is True
    assert result["letter_grade"] == "A"

    with pytest.raises(ValueError, match="raw_score cannot exceed max_score"):
        Assessment(
            "A2",
            learner_id="L1",
            course_id="C1",
            raw_score=60,
            max_score=50,
            grading_strategy=strategy,
        )


def test_singleton_app_config_identity() -> None:
    config1 = AppConfig.get_instance(environment="production", default_page_size=10)
    config2 = AppConfig.get_instance()

    assert id(config1) == id(config2)
    assert config2.environment == "production"
    assert config2.default_page_size == 10


def test_support_ticket_factory_creates_specialized_types() -> None:
    tech = SupportTicketFactory.create_ticket("technical", "L1", "Cannot log in")
    billing = SupportTicketFactory.create_ticket("billing", "L1", "Billing mismatch")
    inquiry = SupportTicketFactory.create_ticket("course", "L1", "Need syllabus")

    assert isinstance(tech, TechnicalSupportTicket)
    assert isinstance(billing, BillingSupportTicket)
    assert isinstance(inquiry, CourseInquiryTicket)

    assert tech.priority is TicketPriority.HIGH
    assert billing.priority is TicketPriority.MEDIUM
    assert inquiry.priority is TicketPriority.LOW


def test_support_ticket_factory_invalid_type() -> None:
    with pytest.raises(ValueError, match="Unsupported ticket_type"):
        SupportTicketFactory.create_ticket("unknown", "L1", "Example")


def test_pass_fail_competency_strategy_logic() -> None:
    result = PassFailCompetencyStrategy().calculate(39, 50)
    assert result == {"percentage": 78.0, "competent": False}

    competent_result = PassFailCompetencyStrategy().calculate(40, 50)
    assert competent_result == {"percentage": 80.0, "competent": True}


def test_weighted_assessment_strategy_logic() -> None:
    strategy = WeightedAssessmentStrategy(weight=0.5, pass_threshold=45.0)

    result = strategy.calculate(80, 100)

    assert result == {
        "percentage": 80.0,
        "weighted_percentage": 40.0,
        "passed": False,
    }

    with pytest.raises(ValueError, match="weight must be positive"):
        WeightedAssessmentStrategy(weight=0)
