"""
scheduler_service.py
--------------------
Manages per-bot auto-posting schedules using background daemon threads.

Each active schedule gets its own thread + threading.Event stop-flag.
- start_schedule(...)  → spawns the thread
- stop_schedule(id)    → signals the thread to exit (returns instantly)
- is_running(id)       → True while thread is alive
- restart_all(app)     → called once on Flask startup to re-arm DB schedules
"""

import logging
import threading
import uuid
from datetime import datetime

log = logging.getLogger("scheduler")

# schedule_id -> Event
_stop_events: dict[int, threading.Event] = {}
_lock = threading.Lock()


# ── Public API ────────────────────────────────────────────────────────────────

def start_schedule(app, schedule_id: int, bot_id: int,
                   interval_seconds: int, post_type: str, topic):
    """Spawn a background thread for this schedule (no-op if already running)."""
    with _lock:
        if schedule_id in _stop_events:
            return
        stop_event = threading.Event()
        _stop_events[schedule_id] = stop_event

    t = threading.Thread(
        target=_loop,
        args=(app, schedule_id, bot_id, interval_seconds, post_type, topic, stop_event),
        daemon=True,
        name=f"sched-{schedule_id}",
    )
    t.start()
    log.info(f" Schedule {schedule_id} started — bot {bot_id} every {interval_seconds}s "
          f"({post_type} post)")


def stop_schedule(schedule_id: int):
    """Signal the thread to stop. Returns immediately; thread exits at next wake-up."""
    with _lock:
        event = _stop_events.pop(schedule_id, None)
    if event:
        event.set()
        log.info(f" Schedule {schedule_id} stop signal sent")


def is_running(schedule_id: int) -> bool:
    return schedule_id in _stop_events


def restart_all(app):
    """Re-arm all schedules that were active when Flask last shut down."""
    from models import BotSchedule
    with app.app_context():
        active = BotSchedule.query.filter_by(is_active=True).all()
        for s in active:
            start_schedule(app, s.id, s.bot_id, s.interval_seconds, s.post_type, s.topic)
        if active:
            log.info(f" Re-armed {len(active)} schedule(s) from DB")


# ── Background loop ───────────────────────────────────────────────────────────

def _loop(app, schedule_id, bot_id, interval_seconds, post_type, topic, stop_event):
    """Waits `interval_seconds`, posts, repeats — until stop_event is set."""
    while True:
        # Block for interval_seconds OR until stop is called
        stopped = stop_event.wait(timeout=interval_seconds)
        if stopped:
            break   # stop_schedule() was called

        with app.app_context():
            _do_post(app, schedule_id, bot_id, post_type, topic)

    # Clean up DB flag
    _mark_inactive(app, schedule_id)
    log.info(f" Schedule {schedule_id} thread exiting")


def _do_post(app, schedule_id, bot_id, post_type, topic):
    """Run one scheduled post inside an app context."""
    from extensions import db
    from models import Bot, Post, BotSchedule
    from services.llama_service import generate_tweet

    try:
        bot = db.session.get(Bot, bot_id)
        if not bot:
            log.info(f" Bot {bot_id} not found — skipping")
            return
        if not bot.is_active:
            log.info(f" Bot {bot_id} is paused — skipping this tick")
            return

        content = generate_tweet(bot, topic)

        if post_type == "video":
            vid_filename = f"{bot.username}_{uuid.uuid4().hex[:8]}.mp4"
            vid_path     = app.root_path + f"/static/videos/{vid_filename}"
            post = Post(
                bot_id      = bot_id,
                content     = content,
                media_type  = "video",
                media_path  = vid_filename,
                post_status = "pending",
            )
            bot.statuses_count += 1
            db.session.add(post)
            db.session.commit()

            # Kick off video gen in yet another daemon thread
            from routes.posts import _video_thread
            vt = threading.Thread(
                target = _video_thread,
                args   = (app, post.id, bot.persona, content, vid_path),
                daemon = True,
            )
            vt.start()
        else:
            post = Post(bot_id=bot_id, content=content)
            bot.statuses_count += 1
            db.session.add(post)
            db.session.commit()

        # Update last_post_at on the schedule row
        sched = db.session.get(BotSchedule, schedule_id)
        if sched:
            sched.last_post_at = datetime.utcnow()
            db.session.commit()

        log.info(f" Bot @{bot.username} posted (schedule {schedule_id}, type={post_type})")

    except Exception as exc:
        log.info(f" Error in schedule {schedule_id}: {exc}")


def _mark_inactive(app, schedule_id):
    """Mark the schedule row inactive after the thread exits naturally."""
    try:
        from extensions import db
        from models import BotSchedule
        with app.app_context():
            sched = db.session.get(BotSchedule, schedule_id)
            if sched and sched.is_active:
                sched.is_active = False
                db.session.commit()
    except Exception:
        pass
