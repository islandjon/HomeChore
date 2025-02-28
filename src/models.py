from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for many-to-many relationship between Chore and User
chore_assignees = db.Table('chore_assignees',
    db.Column('chore_id', db.Integer, db.ForeignKey('chores.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class Household(db.Model):
    __tablename__ = 'households'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, default="Default Household")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship("User", backref="household", lazy=True)
    chores = db.relationship("Chore", backref="household", lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    avatar = db.Column(db.String(255), nullable=True, default="default_avatar.png")
    color = db.Column(db.String(7), nullable=False, default="#3498db")  # Default color blue
    birthdate = db.Column(db.Date, nullable=True)  # New birthdate field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # household = db.relationship("Household", backref="users")


class Chore(db.Model):
    __tablename__ = 'chores'
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="No description provided.")
    # New column for storing specific due days, e.g., "Mon,Wed,Fri"
    due_days = db.Column(db.String(255), nullable=True)
    cooldown = db.Column(db.Integer, nullable=True, default=1)
    last_completed = db.Column(db.DateTime, default=None)
    # This field holds the currently assigned user ID
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Many-to-many relationship for allowed assignees
    assignees = db.relationship('User', secondary=chore_assignees,
                                backref=db.backref('assigned_chores', lazy='dynamic'))
    notifications = db.relationship("Notification", backref="chore", lazy=True)
    # Relationship to easily access the current assigned user as an object
    current_assignee = db.relationship("User", foreign_keys=[assigned_to], lazy=True)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chores.id'), nullable=True)
    message = db.Column(db.Text, nullable=False, default="No message provided.")
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChoreCompletion(db.Model):
    __tablename__ = 'chore_completions'
    id = db.Column(db.Integer, primary_key=True)
    chore_id = db.Column(db.Integer, db.ForeignKey('chores.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
