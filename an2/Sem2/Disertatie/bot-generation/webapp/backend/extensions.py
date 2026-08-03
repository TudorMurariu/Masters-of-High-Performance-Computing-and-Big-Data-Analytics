"""Shared Flask extensions — imported by both app.py and models.py to avoid circular imports."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
