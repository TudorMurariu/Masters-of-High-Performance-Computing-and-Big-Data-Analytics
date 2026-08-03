import threading
import uuid
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Bot
from services.llama_service import generate_profile_data

generate_bp = Blueprint("generate", __name__)


# ── Model-status endpoint (diagnostic) ───────────────────────────────────────

@generate_bp.route("/model-status", methods=["GET"])
def model_status():
    """
    Returns the current state of the image pipeline.
    Call this to diagnose why profile pictures aren't generating.
    """
    import sys
    from services.flux_service import get_pipeline_status

    status = get_pipeline_status()

    # Extra: check if diffusers/torch are even importable
    checks = {}
    for pkg in ("torch", "diffusers", "transformers", "accelerate"):
        checks[pkg] = pkg in sys.modules or _can_import(pkg)

    import torch as _torch
    status["cuda_available"] = _torch.cuda.is_available()
    status["python"]         = sys.executable
    status["packages"]       = checks
    return jsonify(status)


def _can_import(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


# ── Background thread: generate profile pic after bot is already saved ────────

def _pic_thread(app, bot_id: int, display_name: str, persona: str, pic_path: str):
    """Runs in a daemon thread. Generates the image and updates pic_status in DB."""
    from services.flux_service import generate_profile_pic

    with app.app_context():
        try:
            success = generate_profile_pic(display_name, persona, pic_path)
            bot = db.session.get(Bot, bot_id)
            if bot:
                bot.pic_status = "ready" if success else "failed"
                db.session.commit()
                print(f"[IMG] Bot {bot_id} (@{bot.username}) pic {'ready' if success else 'failed (placeholder)'}")
        except Exception as exc:
            print(f"[IMG] Thread error bot {bot_id}: {exc}")
            try:
                bot = db.session.get(Bot, bot_id)
                if bot:
                    bot.pic_status = "failed"
                    db.session.commit()
            except Exception:
                pass


# ── Generate bot (text is synchronous, image is async) ────────────────────────

@generate_bp.route("/bot", methods=["POST"])
def generate_bot():
    data    = request.get_json(silent=True) or {}
    persona = data.get("persona", "general")

    # 1. Generate text profile via Llama (fast — a few seconds)
    try:
        profile = generate_profile_data(persona)
    except Exception as e:
        return jsonify({"error": f"Llama generation failed: {e}"}), 500

    # 2. Deduplicate username
    base     = profile.get("username", f"user_{uuid.uuid4().hex[:6]}")
    username = base
    n = 1
    while Bot.query.filter_by(username=username).first():
        username = f"{base}_{n}"
        n += 1

    # 3. Prepare image path (placeholder written by background thread too)
    pic_filename = f"{username}.png"
    pic_path     = current_app.root_path + f"/static/profile_pics/{pic_filename}"

    # 4. Create bot with pic_status="pending" — return immediately to frontend
    stats = profile.get("fake_stats", {})
    bot   = Bot(
        username          = username,
        display_name      = profile.get("display_name", username),
        bio               = profile.get("bio", ""),
        profile_pic       = pic_filename,
        pic_status        = "pending",
        persona           = persona,
        followers_count   = int(stats.get("followers_count", 100)),
        friends_count     = int(stats.get("friends_count",   50)),
        statuses_count    = int(stats.get("statuses_count",  200)),
        favourites_count  = int(stats.get("favourites_count", 500)),
        listed_count      = int(stats.get("listed_count",    5)),
    )
    db.session.add(bot)
    db.session.commit()

    # 5. Kick off image generation in the background
    app = current_app._get_current_object()
    t   = threading.Thread(
        target  = _pic_thread,
        args    = (app, bot.id, bot.display_name, persona, pic_path),
        daemon  = True,
    )
    t.start()

    return jsonify(bot.to_dict())


# ── Re-generate pic for an existing bot ──────────────────────────────────────

@generate_bp.route("/bot/<int:bot_id>/regen-pic", methods=["POST"])
def regen_pic(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.pic_status == "pending":
        return jsonify({"message": "Already generating"}), 409

    pic_path       = current_app.root_path + f"/static/profile_pics/{bot.profile_pic}"
    bot.pic_status = "pending"
    db.session.commit()

    app = current_app._get_current_object()
    t   = threading.Thread(
        target = _pic_thread,
        args   = (app, bot.id, bot.display_name, bot.persona, pic_path),
        daemon = True,
    )
    t.start()
    return jsonify({"message": "Generating…", "pic_status": "pending"})
