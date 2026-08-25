import time
import logging


class BugzotMonitor:
	_instance = None

	@classmethod
	def get_instance(cls):
		if cls._instance is None:
			cls._instance = cls()
		return cls._instance

	def __init__(self):
		self.events = []
		self.metrics = {
			"total_processed": 0,
			"success": 0,
			"rejected": 0,
			"total_time_ms": 0,
		}

	def log_event(self, category: str, message: str, severity: str = "INFO"):
		self.events.append(
			{
				"timestamp": time.time(),
				"category": category,
				"message": message,
				"severity": severity,
			}
		)

	def print_formatted_report(self):
		print("\n--- BUGZOT OPERATIONAL REPORT ---")
		print(f"Total Processed: {self.metrics['total_processed']}")
		print(
			f"Success: {self.metrics['success']} | Rejected: {self.metrics['rejected']}"
		)
		print("Recent Events:")
		for event in self.events[-5:]:
			print(f"[{event['severity']}] {event['category']}: {event['message']}")
		print("---------------------------------\n")
