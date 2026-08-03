import threading
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Bot, Post
from services.llama_service import generate_tweet

posts_bp = Blueprint("posts", __name__)


# ── Background thread: generate video after post already exists ───────────────

def _video_thread(app, post_id: int, persona: str, topic: str, vid_path: str):
    """
    Generates a video clip (or black-frame placeholder) and updates the post.

    If a valid file was written   → post_status='ready', media_path kept
    If nothing could be written   → post_status='ready', media_type/path cleared
                                    (post degrades silently to text-only)
    On unexpected exception       → same graceful degradation
    """
    import os
    from services.video_service import generate_video

    with app.app_context():
        try:
            generate_video(persona, topic, vid_path)
        except Exception as exc:
            print(f"[VID] Thread error post {post_id}: {exc}")

        # Check whether a real file landed on disk (any size > 500 bytes = valid)
        file_ok = os.path.exists(vid_path) and os.path.getsize(vid_path) > 500

        try:
            post = db.session.get(Post, post_id)
            if post:
                post.post_status = "ready"
                if not file_ok:
                    # Degrade to text-only rather than showing an error
                    post.media_type = None
                    post.media_path = None
                    print(f"[VID] Post {post_id}: no file written — degraded to text post")
                else:
                    print(f"[VID] Post {post_id}: video ready → {vid_path}")
                db.session.commit()
        except Exception as exc:
            print(f"[VID] DB update error post {post_id}: {exc}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@posts_bp.route("/feed")
def feed():
    page    = request.args.get("page", 1, type=int)
    result  = (Post.query
               .join(Bot)
               .filter(Bot.is_active == True)
               .order_by(Post.created_at.desc())
               .paginate(page=page, per_page=20, error_out=False))
    return jsonify({
        "posts":    [p.to_dict() for p in result.items],
        "has_next": result.has_next,
        "total":    result.total,
    })


@posts_bp.route("/bot/<int:bot_id>")
def bot_posts(bot_id):
    Bot.query.get_or_404(bot_id)
    posts = (Post.query
             .filter_by(bot_id=bot_id)
             .order_by(Post.created_at.desc())
             .all())
    return jsonify([p.to_dict() for p in posts])


@posts_bp.route("/generate/<int:bot_id>", methods=["POST"])
def generate_post(bot_id):
    bot   = Bot.query.get_or_404(bot_id)
    data  = request.get_json(silent=True) or {}
    topic = data.get("topic") or None

    try:
        content = generate_tweet(bot, topic)
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500

    post = Post(bot_id=bot_id, content=content)
    bot.statuses_count += 1
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())


@posts_bp.route("/generate-video/<int:bot_id>", methods=["POST"])
def generate_video_post(bot_id):
    """
    1. Ask Llama for a tweet matching the bot's persona (text is fast).
    2. Persist the post immediately with post_status='pending'.
    3. Kick off LTX-Video in a background thread; update status when done.
    4. Return the post dict straight away so the admin panel can display it.
    """
    bot   = Bot.query.get_or_404(bot_id)
    data  = request.get_json(silent=True) or {}
    topic = data.get("topic") or None

    # 1. Generate tweet text
    try:
        content = generate_tweet(bot, topic)
    except Exception as e:
        return jsonify({"error": f"Text generation failed: {e}"}), 500

    # 2. File path for the video
    import uuid
    vid_filename = f"{bot.username}_{uuid.uuid4().hex[:8]}.mp4"
    vid_path     = current_app.root_path + f"/static/videos/{vid_filename}"

    # 3. Create the post immediately (status=pending, media_type=video)
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

    # 4. Start background generation
    app = current_app._get_current_object()
    t   = threading.Thread(
        target = _video_thread,
        args   = (app, post.id, bot.persona, content, vid_path),
        daemon = True,
    )
    t.start()

    return jsonify(post.to_dict()), 202   # 202 Accepted


@posts_bp.route("/<int:post_id>/status")
def post_status(post_id):
    """Lightweight polling endpoint — returns only id + post_status + media_path."""
    post = Post.query.get_or_404(post_id)
    return jsonify({
        "id":          post.id,
        "post_status": post.post_status or "ready",
        "media_path":  f"/static/videos/{post.media_path}" if post.media_path else None,
    })


@posts_bp.route("/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return jsonify({"likes": post.likes})


@posts_bp.route("/<int:post_id>/repost", methods=["POST"])
def repost_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.reposts += 1
    db.session.commit()
    return jsonify({"reposts": post.reposts})
