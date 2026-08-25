"""Demonstration script for Phase 1 enterprise design patterns."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Assessment, Course, Learner, Registration
from src.patterns import (
    AppConfig,
    PassFailCompetencyStrategy,
    StandardPercentageStrategy,
    SupportTicketFactory,
)


def run_demo() -> None:
    print("=" * 72)
    print("Enterprise Training App - Phase 1 Demonstration")
    print("=" * 72)

    learner = Learner("L-1001", "Ava Johnson", "ava.johnson@example.com")
    course = Course("C-300", "Enterprise Python", 2)
    registration = Registration("R-5001", learner, course)

    if course.has_available_slot():
        course.increment_enrolment()
        learner.add_course(course)

    print("\n[Domain Models]")
    print(f"Learner: {learner.name} ({learner.email})")
    print(f"Course: {course.title} | Capacity: {course.capacity}")
    print(f"Registration Status: {registration.status.value}")
    print(f"Enrolled Count: {course.enrolled_count}")

    AppConfig.reset_instance()
    config1 = AppConfig.get_instance(environment="production", db_url="postgresql://db")
    config2 = AppConfig.get_instance()

    print("\n[Singleton Pattern]")
    print(f"config1 is config2 -> {config1 is config2}")
    print(f"Environment: {config1.environment} | DB: {config1.db_url}")

    tech_ticket = SupportTicketFactory.create_ticket(
        "technical",
        learner_id=learner.learner_id,
        description="Unable to access course materials.",
    )
    billing_ticket = SupportTicketFactory.create_ticket(
        "billing",
        learner_id=learner.learner_id,
        description="Invoice amount seems incorrect.",
    )

    print("\n[Factory Pattern]")
    print(f"Technical Ticket: {tech_ticket.ticket_id} | {tech_ticket.priority.value}")
    print(f"Billing Ticket: {billing_ticket.ticket_id} | {billing_ticket.priority.value}")

    assessment_standard = Assessment(
        "A-9001",
        learner_id=learner.learner_id,
        course_id=course.course_id,
        raw_score=42,
        max_score=50,
        grading_strategy=StandardPercentageStrategy(),
    )
    assessment_competency = Assessment(
        "A-9002",
        learner_id=learner.learner_id,
        course_id=course.course_id,
        raw_score=42,
        max_score=50,
        grading_strategy=PassFailCompetencyStrategy(),
    )

    print("\n[Strategy Pattern]")
    print(f"Standard Result: {assessment_standard.calculate_result()}")
    print(f"Competency Result: {assessment_competency.calculate_result()}")

    print("\nDemo completed successfully.")


if __name__ == "__main__":
    run_demo()
