from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Household(db.Model):
    __tablename__ = 'households'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, default="Default Household")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One household has many users and chores
    users = db.relationship("User", backref="household", lazy=True)
    chores = db.relationship("Chore", backref="household", lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notifications for this user
    notifications = db.relationship("Notification", backref="user", lazy=True)

class Chore(db.Model):
    __tablename__ = 'chores'
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="No description provided.")
    # Default frequency is 1 day
    frequency = db.Column(db.Interval, default=timedelta(days=1))
    last_completed = db.Column(db.DateTime, default=None)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to get the user who last completed the chore.
    completer = db.relationship("User", foreign_keys=[assigned_to], backref="completed_chores", lazy=True)
    
    # Notifications associated with this chore
    notifications = db.relationship("Notification", backref="chore", lazy=True)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chores.id'), nullable=True)
    message = db.Column(db.Text, nullable=False, default="No message provided.")
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
