from __future__ import annotations

from queue import Queue
from threading import Event, Thread

from main import SecurityMonitorSystem


class _ExplodingAnalyzer:
    def __init__(self, stop_event: Event):
        self.stop_event = stop_event

    def analyze_repository(self, _data):
        self.stop_event.set()
        raise RuntimeError("boom")

    def analyze_cve(self, _data):
        self.stop_event.set()
        raise RuntimeError("boom")


class _DummyReportGenerator:
    def save_analysis_result(self, _result, _source_type):
        return None


def test_run_analysis_calls_task_done_on_exception():
    system = SecurityMonitorSystem.__new__(SecurityMonitorSystem)
    system.stop_event = Event()
    system.data_queue = Queue()
    system.report_generator = _DummyReportGenerator()
    system.analyzer = _ExplodingAnalyzer(system.stop_event)

    system.data_queue.put(("repository", {"name": "owner/repo"}))

    worker = Thread(target=system.run_analysis, daemon=True)
    worker.start()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert system.data_queue.unfinished_tasks == 0
