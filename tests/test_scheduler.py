import unittest

from rc_vision_ai.scheduler import SequentialScheduler, TaskState


class SchedulerTests(unittest.TestCase):
    def test_tasks_run_in_order(self):
        order = []
        scheduler = SequentialScheduler()
        scheduler.submit("first", lambda: order.append("first"))
        scheduler.submit("second", lambda: order.append("second"))

        tasks = scheduler.run_all()

        self.assertEqual(order, ["first", "second"])
        self.assertEqual([t.state for t in tasks], [TaskState.COMPLETED, TaskState.COMPLETED])

    def test_failure_does_not_stop_queue(self):
        scheduler = SequentialScheduler()

        def fail():
            raise RuntimeError("expected test failure")

        scheduler.submit("broken", fail)
        scheduler.submit("works", lambda: None)
        tasks = scheduler.run_all()

        self.assertEqual(tasks[0].state, TaskState.FAILED)
        self.assertIn("expected test failure", tasks[0].error or "")
        self.assertEqual(tasks[1].state, TaskState.COMPLETED)

    def test_empty_task_name_rejected(self):
        scheduler = SequentialScheduler()
        with self.assertRaises(ValueError):
            scheduler.submit("  ", lambda: None)

    def test_snapshot_starts_queued(self):
        scheduler = SequentialScheduler()
        scheduler.submit("pending", lambda: None)
        self.assertEqual(scheduler.snapshot()[0]["state"], "queued")


if __name__ == "__main__":
    unittest.main()
