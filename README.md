# FocusFlow — Arbiter Hacks V1 (General Track)

Solo project for Umar Shareef. Deadline: Dec 20, 2026, 9:00pm PST (per 2026-10-28 check; re-verify on the live Devpost page before submitting).

## What it is

An offline, honest study planner. Add tasks with minutes, mark them done with a
button, watch real progress, and run a focus timer that counts only time while
it is running. No account, no cloud, no invented users, no external API, no
keys, no seeded stats — every number comes from real actions in the app.

## Features (all working, locally tested)

1. **Tasks** — add a task with a title and minutes; validation rejects an empty
   title or non-positive minutes.
2. **Complete-task button** — each unfinished task has its own Complete button;
   completed tasks are struck through and marked "✓ done", and progress
   (tasks done, minutes done, %) updates from real completions only.
3. **Local JSON persistence** — tasks and paused focus time are saved to
   `data/focusflow.json` (created on first save) and reloaded on restart, so
   closing the app does not lose work. The `data/` folder is gitignored, so a
   user's real tasks are never committed to a public repo. A running focus
   segment is deliberately NOT persisted until paused, so a restart never
   invents focus time.
4. **Focus timer** — Start / Pause / Reset in the UI. Pause stops the clock
   (paused time does not count); Reset clears the total. The server exposes
   `/api/focus` (start / pause / reset) and the summary reports
   `focused_minutes` alongside task progress.
5. **Progress bar and next task** — the UI shows a progress bar, done/total
   minutes, progress %, and the next unfinished task.

## Stack and how to run

Python stdlib only + plain HTML/JS. No dependencies to install.

```bash
cd ~/workspace/arbiter-hacks
python3 src/server.py
# then open http://localhost:8003/
```

The server honours `$PORT` (default 8003) and `$FOCUSFLOW_DATA` (default
`data/focusflow.json` under the project root).

## Tests

```bash
python3 -m unittest discover -s tests
# 8/8 pass (2026-10-29): add/progress, empty state, validation,
# complete-by-id + unknown id, JSON persistence round-trip (including id
# uniqueness after reload), missing-file load, focus timer counting only
# running time, idempotent start.
```

A server smoke test was also run 2026-10-29 against a temporary data file:
health ok, task add, complete-by-id, focus start/pause/reset, and persistence
across a server restart all passed; secret scan clean (no keys, tokens, or
credentials anywhere in the project).

## Honest limits

- Single-user, single-machine app: there is no sync, no sharing, and no
  multi-device support by design.
- Focus time is counted by the timer in this app only; it cannot verify
  attention outside the app, and it does not claim to.
- No demo video, public repo, or Devpost submission exists yet.

## Status — NOT submitted

Remaining before submission (not done in this task, by instruction): public
repo push (verify no `data/` or secrets in it), a 2–3 min demo video recorded
by Umar as a real screen capture, a Devpost description, and Umar's final
approval. See `docs/DEMO-SCRIPT.md` and `docs/PLAN.md`.
