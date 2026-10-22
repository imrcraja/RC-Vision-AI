"""Small sequential scheduler; deliberately uses only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Callable


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    name: str
    action: Callable[[], None]
    state: TaskState = TaskState.QUEUED
    error: str | None = None
    created_at: float = field(default_factory=monotonic)
    started_at: float | None = None
    finished_at: float | None = None


class SequentialScheduler:
    """Runs at most one task at a time; never invents a percentage."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._lock = Lock()

    def submit(self, name: str, action: Callable[[], None]) -> Task:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Task name cannot be empty.")
        task = Task(name=clean_name, action=action)
        with self._lock:
            self._tasks.append(task)
        return task

    def snapshot(self) -> list[dict[str, str | None]]:
        with self._lock:
            return [
                {"name": t.name, "state": t.state.value, "error": t.error}
                for t in self._tasks
            ]

    def run_next(self) -> Task | None:
        with self._lock:
            task = next((t for t in self._tasks if t.state == TaskState.QUEUED), None)
            if task is None:
                return None
            task.state = TaskState.RUNNING
            task.started_at = monotonic()

        try:
            task.action()
        except Exception as exc:  # keep the queue usable after an individual failure
            task.error = f"{type(exc).__name__}: {exc}"
            task.state = TaskState.FAILED
        else:
            task.state = TaskState.COMPLETED
        finally:
            task.finished_at = monotonic()
        return task

    def run_all(self) -> list[Task]:
        finished: list[Task] = []
        while True:
            task = self.run_next()
            if task is None:
                return finished
            finished.append(task)
