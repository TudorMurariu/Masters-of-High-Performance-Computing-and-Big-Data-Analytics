"""SQLAlchemy ORM models for BotFarm Simulator."""
from datetime import datetime
from extensions import db


class Bot(db.Model):
    __tablename__ = "bots"

    id                    = db.Column(db.Integer,  primary_key=True)
    username              = db.Column(db.String(50),  unique=True, nullable=False)
    display_name          = db.Column(db.String(100), nullable=False)
    bio                   = db.Column(db.Text,    default="")
    profile_pic           = db.Column(db.String(200))
    pic_status            = db.Column(db.String(10), default="pending")  # pending|ready|failed
    persona               = db.Column(db.String(50),  default="general")
    # Metadata stats (used by detector)
    followers_count       = db.Column(db.Integer, default=0)
    friends_count         = db.Column(db.Integer, default=0)
    statuses_count        = db.Column(db.Integer, default=0)
    favourites_count      = db.Column(db.Integer, default=0)
    listed_count          = db.Column(db.Integer, default=0)
    verified              = db.Column(db.Integer, default=0)
    default_profile       = db.Column(db.Integer, default=1)
    default_profile_image = db.Column(db.Integer, default=0)
    geo_enabled           = db.Column(db.Integer, default=0)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)
    is_active             = db.Column(db.Boolean,  default=True)
    # Detector results
    detection_score       = db.Column(db.Float,      nullable=True)
    detection_label       = db.Column(db.String(10), nullable=True)

    posts    = db.relationship("Post",    backref="bot", lazy=True,
                               cascade="all, delete-orphan")
    messages = db.relationship("Message", backref="bot", lazy=True,
                               cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":              self.id,
            "username":        self.username,
            "display_name":    self.display_name,
            "bio":             self.bio,
            "profile_pic":     f"/static/profile_pics/{self.profile_pic}" if self.profile_pic else None,
            "pic_status":      self.pic_status or "ready",
            "persona":         self.persona,
            "followers_count": self.followers_count,
            "friends_count":   self.friends_count,
            "statuses_count":  self.statuses_count,
            "created_at":      self.created_at.isoformat(),
            "is_active":       self.is_active,
            "detection_score": self.detection_score,
            "detection_label": self.detection_label,
            "post_count":      len(self.posts),
        }


class Post(db.Model):
    __tablename__ = "posts"

    id          = db.Column(db.Integer, primary_key=True)
    bot_id      = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    media_type  = db.Column(db.String(20),  nullable=True)   # "video" | None
    media_path  = db.Column(db.String(200), nullable=True)
    post_status = db.Column(db.String(10),  default="ready") # ready|pending|failed
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    likes       = db.Column(db.Integer, default=0)
    reposts     = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id":          self.id,
            "bot_id":      self.bot_id,
            "bot": {
                "username":        self.bot.username,
                "display_name":    self.bot.display_name,
                "profile_pic":     f"/static/profile_pics/{self.bot.profile_pic}"
                                   if self.bot.profile_pic else None,
                "detection_score": self.bot.detection_score,
                "detection_label": self.bot.detection_label,
            },
            "content":     self.content,
            "media_type":  self.media_type,
            "media_path":  f"/static/videos/{self.media_path}" if self.media_path else None,
            "post_status": self.post_status or "ready",
            "created_at":  self.created_at.isoformat(),
            "likes":       self.likes,
            "reposts":     self.reposts,
        }


class BotSchedule(db.Model):
    __tablename__ = "bot_schedules"

    id               = db.Column(db.Integer, primary_key=True)
    bot_id           = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)
    interval_seconds = db.Column(db.Integer, nullable=False)   # min 30
    post_type        = db.Column(db.String(10), default="text") # text | video
    topic            = db.Column(db.String(200), nullable=True)
    is_active        = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    last_post_at     = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        from datetime import timedelta
        next_at = None
        if self.last_post_at:
            next_at = (self.last_post_at + timedelta(seconds=self.interval_seconds)).isoformat()
        return {
            "id":               self.id,
            "bot_id":           self.bot_id,
            "interval_seconds": self.interval_seconds,
            "post_type":        self.post_type,
            "topic":            self.topic,
            "is_active":        self.is_active,
            "created_at":       self.created_at.isoformat(),
            "last_post_at":     self.last_post_at.isoformat() if self.last_post_at else None,
            "next_post_at":     next_at,
        }


class Message(db.Model):
    __tablename__ = "messages"

    id         = db.Column(db.Integer, primary_key=True)
    bot_id     = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    role       = db.Column(db.String(10), nullable=False)  # "user" | "assistant"
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "role":       self.role,
            "content":    self.content,
            "created_at": self.created_at.isoformat(),
        }
