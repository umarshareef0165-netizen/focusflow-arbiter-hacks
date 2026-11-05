import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from planner import FocusTimer, Planner


class T(unittest.TestCase):
    def test_add_and_progress(self):
        p = Planner(); p.add("Python", 25); p.add("ML", 25); p.complete(0)
        self.assertEqual(p.progress_pct(), 50.0); self.assertEqual(p.next_task().title, "ML")

    def test_empty(self):
        p = Planner(); self.assertEqual(p.progress_pct(), 0.0); self.assertIsNone(p.next_task())

    def test_validation(self):
        p = Planner()
        with self.assertRaises(ValueError): p.add(" ", 10)
        with self.assertRaises(ValueError): p.add("x", 0)

    def test_complete_by_id_and_unknown_id(self):
        p = Planner(); a = p.add("A", 10); p.add("B", 20)
        p.complete_by_id(a.id)
        self.assertTrue(p.tasks[0].done); self.assertFalse(p.tasks[1].done)
        self.assertEqual(p.progress_pct(), 33.3)
        with self.assertRaises(KeyError): p.complete_by_id(9999)

    def test_json_persistence_round_trip(self):
        p = Planner(); p.add("Python", 25); p.add("ML", 25)
        p.complete_by_id(1)
        p.focus._completed_seconds = 90.0  # paused time only, as persisted
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "focusflow.json")
            p.save(path)
            q = Planner.load(path)
        self.assertEqual([t.title for t in q.tasks], ["Python", "ML"])
        self.assertTrue(q.tasks[0].done); self.assertFalse(q.tasks[1].done)
        self.assertEqual(q.progress_pct(), 50.0)
        self.assertEqual(q.focus.status()["elapsed_seconds"], 90)
        # New tasks after reload keep unique ids (no id reuse / collision).
        t = q.add("New", 5)
        self.assertNotIn(t.id, [1, 2])

    def test_load_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p = Planner.load(os.path.join(d, "nope.json"))
        self.assertEqual(p.tasks, []); self.assertEqual(p.progress_pct(), 0.0)

    def test_focus_timer_counts_only_running_time(self):
        now = [1000.0]
        timer = FocusTimer(time_fn=lambda: now[0])
        timer.start(); now[0] += 60; timer.pause()
        now[0] += 999  # paused time must NOT count
        timer.start(); now[0] += 30; timer.pause()
        self.assertEqual(timer.status()["elapsed_seconds"], 90)
        self.assertFalse(timer.status()["running"])
        timer.reset()
        self.assertEqual(timer.status()["elapsed_seconds"], 0)

    def test_focus_timer_start_is_idempotent(self):
        now = [0.0]
        timer = FocusTimer(time_fn=lambda: now[0])
        timer.start(); now[0] += 10; timer.start(); now[0] += 10; timer.pause()
        self.assertEqual(timer.status()["elapsed_seconds"], 20)


if __name__ == "__main__":
    unittest.main()
