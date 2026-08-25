import sys
from pathlib import Path
import cProfile
import pstats

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Course, Learner
from src.engine import RegistrationEngine

def main():
	# 1. Initialize course and 1000 learners
	course = Course("C-PERF", "High-Throughput Systems", capacity=800, active_status=True)
	learners = [
		Learner(f"L{i}", f"Learner {i}", f"learner{i}@enterprise.com")
		for i in range(1, 1001)
	]
	engine = RegistrationEngine(courses=[course], learners=learners)

	# 2. Generate 1500 requests (1000 unique + 500 duplicates)
	requests = [
		{"learner_id": f"L{i}", "course_id": "C-PERF", "name": f"Learner {i}", "email": f"learner{i}@enterprise.com"}
		for i in range(1, 1001)
	]
	requests.extend([
		{"learner_id": f"L{i}", "course_id": "C-PERF", "name": f"Learner {i}", "email": f"learner{i}@enterprise.com"}
		for i in range(1, 501)
	])

	# 3. Profile engine execution
	profiler = cProfile.Profile()
	profiler.enable()
	summary = engine.process_concurrently(requests, max_workers=4)
	profiler.disable()

	# 4. Print execution metrics
	print(f"Total Processed: {summary.get('total_processed', len(requests))}")
	print(f"Confirmed Count: {summary.get('confirmed_count', 0)}")
	print(f"Rejected Count:  {summary.get('rejected_count', 0)}")

	# 5. Print top 15 cumulative time stats
	stats = pstats.Stats(profiler)
	stats.sort_stats("cumtime")
	stats.print_stats(15)

if __name__ == "__main__":
	main()
