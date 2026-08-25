import sys
from pathlib import Path
import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Assessment, Course, Learner
from src.patterns import StandardPercentageStrategy
from src.engine import RegistrationEngine
from src.bugzot import BugzotMonitor

def test_end_to_end_registration_lifecycle():
    # 1. Reset telemetry
    monitor = BugzotMonitor.get_instance()
    monitor.events.clear()

    # 2. Setup Course and Learner
    course = Course("C-TEST", "Enterprise Architecture", capacity=1, active_status=True)
    learner = Learner("L101", "Ava Johnson", "ava.johnson@example.com")

    # 3. Initialize engine and process registration
    engine = RegistrationEngine(courses=[course], learners=[learner])
    requests = [
        {"learner_id": "L101", "course_id": "C-TEST", "name": "Ava Johnson", "email": "ava.johnson@example.com"}
    ]
    summary = engine.process_concurrently(requests, max_workers=1)

    # 4. Assert batch output and capacity state
    assert course.enrolled_count == 1

    # 5. Evaluate assessment with strategy
    strategy = StandardPercentageStrategy()
    assessment = Assessment("A101", "L101", "C-TEST", raw_score=45, max_score=50, grading_strategy=strategy)
    result = assessment.calculate_result()

    # 6. Assert grading results
    assert result["passed"] is True
    assert result["percentage"] == 90.0
