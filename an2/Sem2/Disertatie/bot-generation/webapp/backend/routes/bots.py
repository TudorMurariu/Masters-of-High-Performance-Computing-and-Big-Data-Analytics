from flask import Blueprint, jsonify
from extensions import db
from models import Bot

bots_bp = Blueprint("bots", __name__)


@bots_bp.route("/")
def list_bots():
    bots = Bot.query.order_by(Bot.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bots])


@bots_bp.route("/<int:bot_id>")
def get_bot(bot_id):
    return jsonify(Bot.query.get_or_404(bot_id).to_dict())


@bots_bp.route("/by-username/<username>")
def get_by_username(username):
    bot = Bot.query.filter_by(username=username).first_or_404()
    return jsonify(bot.to_dict())


@bots_bp.route("/<int:bot_id>", methods=["DELETE"])
def delete_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    db.session.delete(bot)
    db.session.commit()
    return jsonify({"success": True})


@bots_bp.route("/<int:bot_id>/toggle", methods=["POST"])
def toggle_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    bot.is_active = not bot.is_active
    db.session.commit()
    return jsonify({"is_active": bot.is_active})
