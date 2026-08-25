#!/usr/bin/env python3
"""Application profiler for concurrent registration processing."""

from __future__ import annotations

import cProfile
import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine import RegistrationEngine
from src.models import Course, Learner


def main() -> None:
    courses = {"C-PROFILE": Course("C-PROFILE", "High-Volume Course", capacity=500)}
    learners = {
        f"L{index}": Learner(
            learner_id=f"L{index}",
            name=f"Learner {index}",
            email=f"learner{index}@example.com",
        )
        for index in range(1000)
    }
    engine = RegistrationEngine(courses=courses, learners=learners)

    requests: list[dict[str, str]] = [
        {
            "registration_id": f"R{index}",
            "learner_id": f"L{index}",
            "course_id": "C-PROFILE",
        }
        for index in range(700)
    ]
    requests.extend(
        [
            {
                "registration_id": f"R-DUP-{index}",
                "learner_id": f"L{index}",
                "course_id": "C-PROFILE",
            }
            for index in range(300)
        ]
    )

    profile = cProfile.Profile()
    profile.enable()
    engine.process_concurrently(requests, max_workers=4)
    profile.disable()

    stats = pstats.Stats(profile).sort_stats("cumtime")
    stats.print_stats(20)


if __name__ == "__main__":
    main()
