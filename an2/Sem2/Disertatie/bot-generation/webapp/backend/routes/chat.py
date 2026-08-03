from flask import Blueprint, request, jsonify
from extensions import db
from models import Bot, Message
from services.llama_service import chat_with_bot

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/<int:bot_id>", methods=["POST"])
def chat(bot_id):
    bot  = Bot.query.get_or_404(bot_id)
    data = request.get_json(silent=True) or {}
    user_msg   = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not user_msg:
        return jsonify({"error": "message is required"}), 400

    # Load history
    history = (Message.query
               .filter_by(bot_id=bot_id, session_id=session_id)
               .order_by(Message.created_at)
               .all())

    # Save user turn
    db.session.add(Message(bot_id=bot_id, session_id=session_id,
                            role="user", content=user_msg))
    db.session.flush()

    # Get LLM reply
    try:
        reply = chat_with_bot(bot, [m.to_dict() for m in history], user_msg)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Llama failed: {e}"}), 500

    # Save assistant turn
    db.session.add(Message(bot_id=bot_id, session_id=session_id,
                            role="assistant", content=reply))
    bot.statuses_count += 1
    db.session.commit()

    return jsonify({"reply": reply, "session_id": session_id})


@chat_bp.route("/<int:bot_id>/history")
def history(bot_id):
    session_id = request.args.get("session_id", "default")
    msgs = (Message.query
            .filter_by(bot_id=bot_id, session_id=session_id)
            .order_by(Message.created_at)
            .all())
    return jsonify([m.to_dict() for m in msgs])
