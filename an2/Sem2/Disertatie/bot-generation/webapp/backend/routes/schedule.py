from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Bot, BotSchedule
from services.scheduler_service import start_schedule, stop_schedule, is_running

schedule_bp = Blueprint("schedule", __name__)

MIN_INTERVAL = 5    # seconds — absolute floor to prevent accidents


@schedule_bp.route("/", methods=["GET"])
def list_schedules():
    """All active schedules (admin overview)."""
    rows = BotSchedule.query.filter_by(is_active=True).order_by(BotSchedule.created_at.desc()).all()
    return jsonify([{**s.to_dict(), "running": is_running(s.id)} for s in rows])


@schedule_bp.route("/bot/<int:bot_id>", methods=["GET"])
def bot_schedules(bot_id):
    """Active schedules for one bot."""
    Bot.query.get_or_404(bot_id)
    rows = BotSchedule.query.filter_by(bot_id=bot_id, is_active=True).all()
    return jsonify([{**s.to_dict(), "running": is_running(s.id)} for s in rows])


@schedule_bp.route("/", methods=["POST"])
def create_schedule():
    """
    Body: { bot_id, interval_seconds, post_type ("text"|"video"), topic? }
    interval_seconds is clamped to a minimum of 30 s.
    """
    data             = request.get_json(silent=True) or {}
    bot_id           = data.get("bot_id")
    interval_seconds = max(MIN_INTERVAL, int(data.get("interval_seconds", 3600)))
    post_type        = data.get("post_type", "text")
    topic            = data.get("topic") or None

    if not bot_id:
        return jsonify({"error": "bot_id is required"}), 400
    if post_type not in ("text", "video"):
        return jsonify({"error": "post_type must be 'text' or 'video'"}), 400

    Bot.query.get_or_404(bot_id)

    sched = BotSchedule(
        bot_id           = bot_id,
        interval_seconds = interval_seconds,
        post_type        = post_type,
        topic            = topic,
        is_active        = True,
    )
    db.session.add(sched)
    db.session.commit()

    app = current_app._get_current_object()
    start_schedule(app, sched.id, bot_id, interval_seconds, post_type, topic)

    return jsonify({**sched.to_dict(), "running": True}), 201


@schedule_bp.route("/<int:schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id):
    """Stop and permanently remove a schedule."""
    sched = BotSchedule.query.get_or_404(schedule_id)
    stop_schedule(schedule_id)
    sched.is_active = False
    db.session.commit()
    return jsonify({"success": True})
