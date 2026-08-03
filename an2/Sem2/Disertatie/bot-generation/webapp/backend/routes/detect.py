from flask import Blueprint, jsonify
from extensions import db
from models import Bot, Post
from services.detector_service import detect_bot

detect_bp = Blueprint("detect", __name__)


@detect_bp.route("/<int:bot_id>", methods=["POST"])
def detect_single(bot_id):
    bot   = Bot.query.get_or_404(bot_id)
    texts = [p.content for p in Post.query.filter_by(bot_id=bot_id).all()]

    try:
        score, label = detect_bot(bot, texts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    bot.detection_score = score
    bot.detection_label = label
    db.session.commit()
    return jsonify({"score": score, "label": label, "bot_id": bot_id})


@detect_bp.route("/all", methods=["POST"])
def detect_all():
    bots    = Bot.query.all()
    results = []
    for bot in bots:
        texts = [p.content for p in Post.query.filter_by(bot_id=bot.id).all()]
        try:
            score, label = detect_bot(bot, texts)
            bot.detection_score = score
            bot.detection_label = label
            results.append({"bot_id": bot.id, "username": bot.username,
                            "score": score, "label": label})
        except Exception as e:
            results.append({"bot_id": bot.id, "username": bot.username, "error": str(e)})
    db.session.commit()
    return jsonify(results)
