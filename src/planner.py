"""FocusFlow core: offline study planner. Pure logic, no network, no keys.

Honesty rules (kept from the scaffold):
- Progress and focus time come only from real in-app actions.
- Nothing is seeded, no fake users, no fake stats.
- Persistence is a local JSON file only -- no cloud, no account.
"""
import json
import os
import time
from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    minutes: int
    done: bool = False
    id: int = 0

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if self.minutes <= 0:
            raise ValueError("minutes must be positive")

    def to_dict(self):
        return {"id": self.id, "title": self.title,
                "minutes": self.minutes, "done": self.done}

    @classmethod
    def from_dict(cls, data):
        return cls(title=data["title"], minutes=int(data["minutes"]),
                   done=bool(data.get("done", False)),
                   id=int(data.get("id", 0)))


class FocusTimer:
    """Counts only time while running. Pause stops the clock; reset clears it.

    `time_fn` is injectable so tests can advance a fake clock instead of
    waiting for real seconds.
    """

    def __init__(self, time_fn=time.monotonic):
        self._time_fn = time_fn
        self._running_since = None
        self._completed_seconds = 0.0

    def start(self):
        if self._running_since is None:
            self._running_since = self._time_fn()
        return self.status()

    def pause(self):
        if self._running_since is not None:
            self._completed_seconds += self._time_fn() - self._running_since
            self._running_since = None
        return self.status()

    def reset(self):
        self._running_since = None
        self._completed_seconds = 0.0
        return self.status()

    def elapsed_seconds(self):
        total = self._completed_seconds
        if self._running_since is not None:
            total += self._time_fn() - self._running_since
        return total

    def status(self):
        return {
            "running": self._running_since is not None,
            "elapsed_seconds": int(self.elapsed_seconds()),
            "focused_minutes": round(self.elapsed_seconds() / 60, 1),
        }

    def to_dict(self):
        # Only completed (paused) time is persisted; a running segment is
        # not counted until it is paused, so a restart never invents time.
        return {"completed_seconds": self._completed_seconds}

    def load(self, data):
        self._completed_seconds = float(data.get("completed_seconds", 0.0))
        self._running_since = None


@dataclass
class Planner:
    tasks: list = field(default_factory=list)
    focus: FocusTimer = field(default_factory=FocusTimer)
    _next_id: int = 1

    def add(self, title, minutes):
        t = Task(title.strip(), int(minutes), id=self._next_id)
        self._next_id += 1
        self.tasks.append(t)
        return t

    def complete(self, index):
        self.tasks[index].done = True

    def complete_by_id(self, task_id):
        for t in self.tasks:
            if t.id == int(task_id):
                t.done = True
                return t
        raise KeyError(f"no task with id {task_id}")

    def total_minutes(self):
        return sum(t.minutes for t in self.tasks)

    def done_minutes(self):
        return sum(t.minutes for t in self.tasks if t.done)

    def progress_pct(self):
        total = self.total_minutes()
        return round(100 * self.done_minutes() / total, 1) if total else 0.0

    def next_task(self):
        for t in self.tasks:
            if not t.done:
                return t
        return None

    def summary(self):
        nxt = self.next_task()
        out = {
            "tasks": len(self.tasks),
            "done": sum(1 for t in self.tasks if t.done),
            "total_minutes": self.total_minutes(),
            "done_minutes": self.done_minutes(),
            "progress_pct": self.progress_pct(),
            "next": nxt.title if nxt else None,
            "task_list": [t.to_dict() for t in self.tasks],
        }
        out.update(self.focus.status())
        return out

    def to_dict(self):
        return {"next_id": self._next_id,
                "tasks": [t.to_dict() for t in self.tasks],
                "focus": self.focus.to_dict()}

    @classmethod
    def from_dict(cls, data):
        p = cls()
        p.tasks = [Task.from_dict(d) for d in data.get("tasks", [])]
        p._next_id = int(data.get("next_id", 0)) or (
            max((t.id for t in p.tasks), default=0) + 1)
        p.focus.load(data.get("focus", {}))
        return p

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
