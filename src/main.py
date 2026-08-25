"""Demonstration script for enterprise training app phases."""

from __future__ import annotations

from src.bugzot import BugzotMonitor
from src.engine import RegistrationEngine, compare_optimization_benchmark
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


def run_phase2_demo() -> None:
    print("\n" + "=" * 72)
    print("Enterprise Training App - Phase 2 Concurrent Registration")
    print("=" * 72)

    courses = [
        Course("C-401", "Concurrent Python Fundamentals", 3),
        Course("C-402", "Distributed Data Modeling", 10),
    ]
    learners = [
        Learner(f"L-{index:04d}", f"Learner {index}", f"learner{index}@example.com")
        for index in range(1, 13)
    ]

    engine = RegistrationEngine(courses=courses, learners=learners)

    requests = [
        {"registration_id": "R-7001", "learner_id": "L-0001", "course_id": "C-401"},
        {"registration_id": "R-7002", "learner_id": "L-0002", "course_id": "C-401"},
        {"registration_id": "R-7003", "learner_id": "L-0003", "course_id": "C-401"},
        {"registration_id": "R-7004", "learner_id": "L-0004", "course_id": "C-401"},
        {"registration_id": "R-7005", "learner_id": "L-0005", "course_id": "C-402"},
        {"registration_id": "R-7006", "learner_id": "L-0005", "course_id": "C-402"},
        {"registration_id": "R-7007", "learner_id": "L-0006", "course_id": "C-402"},
        {"registration_id": "R-7008", "learner_id": "L-0007", "course_id": "C-402"},
        {"registration_id": "R-7009", "learner_id": "L-0008", "course_id": "C-402"},
        {"registration_id": "R-7010", "learner_id": "L-0009", "course_id": "C-402"},
        {"registration_id": "R-7011", "learner_id": "L-9999", "course_id": "C-402"},
        {"registration_id": "R-7012", "learner_id": "L-0010", "course_id": "C-999"},
    ]

    summary = engine.process_concurrently(requests, max_workers=10)

    print("\n[Concurrent Processing Results]")
    for result in summary["results"]:
        registration = result["registration"]
        registration_id = registration.registration_id if registration else "N/A"
        print(
            f"Thread {result['thread_id']}: {registration_id} -> "
            f"{result['status'].value} ({result['reason']})"
        )

    print("\n[Summary]")
    print(f"Total Processed: {summary['total_processed']}")
    print(f"Successful: {summary['successful_count']}")
    print(f"Rejected/Failed: {summary['rejected_count']}")
    print(f"Rejection Breakdown: {summary['rejection_reasons']}")
    for course in courses:
        print(
            f"Course {course.course_id}: {course.enrolled_count}/{course.capacity} enrolled"
        )
    print(f"Execution Time: {summary['execution_time_seconds']:.6f} seconds")


def run_phase3_demo() -> None:
    print("\n" + "=" * 72)
    print("Enterprise Training App - Phase 3 Bugzot Monitoring")
    print("=" * 72)

    BugzotMonitor.reset_instance()
    monitor = BugzotMonitor.get_instance()
    courses = [Course("C-501", "Bugzot Performance Engineering", 2)]
    learners = [
        Learner("L-2001", "Nina Tran", "nina.tran@example.com"),
        Learner("L-2002", "Omar Lee", "omar.lee@example.com"),
        Learner("L-2003", "Pia Gomez", "pia.gomez@example.com"),
    ]
    engine = RegistrationEngine(courses=courses, learners=learners, monitor=monitor)

    requests = [
        {"registration_id": "R-9001", "learner_id": "L-2001", "course_id": "C-501"},
        {"registration_id": "R-9002", "learner_id": "L-2001", "course_id": "C-501"},
        {"registration_id": "R-9003", "learner_id": "L-2002", "course_id": "C-501"},
        {"registration_id": "R-9004", "learner_id": "L-2003", "course_id": "C-501"},
        {"registration_id": "R-9005", "learner_id": "", "course_id": "C-501"},
    ]
    summary = engine.process_concurrently(requests, max_workers=5)

    print("\n[Bugzot-Monitored Concurrent Results]")
    print(
        f"Total={summary['total_processed']} | "
        f"Success={summary['successful_count']} | Rejected={summary['rejected_count']}"
    )
    print(f"Rejection Breakdown: {summary['rejection_reasons']}")

    print("\n[Bugzot Diagnostic Event Logs]")
    for event in monitor.get_events():
        print(
            f"{event['timestamp']} | {event['level']} | {event['category']} | "
            f"{event['message']} | payload={event['payload']}"
        )

    monitor.print_formatted_report()

    benchmark = compare_optimization_benchmark(1000)
    print("\n[Optimization Benchmark]")
    print(f"Requests: {int(benchmark['total_requests'])}")
    print(f"Unoptimized: {benchmark['unoptimized_seconds']:.6f}s")
    print(f"Optimized:   {benchmark['optimized_seconds']:.6f}s")
    print(f"Speedup:     {benchmark['speedup_factor']:.2f}x")


if __name__ == "__main__":
    run_demo()
    run_phase2_demo()
    run_phase3_demo()
