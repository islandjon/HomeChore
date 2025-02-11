from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import pytz
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@0.0.0.0:5432/choredb')
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')  # Needed for sessions

# Import the models from models.py
from models import db, Household, User, Chore, Notification

# Initialize the database with the app
db.init_app(app)

# Initialize the migration engine
migrate = Migrate(app, db)

@app.route('/')
def dashboard():
    # Get the user's timezone (default to UTC)
    tz_name = session.get('timezone', 'UTC')
    timezone = pytz.timezone(tz_name)
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(timezone)
    today_date = now.date()

    chores = Chore.query.all()
    users = User.query.all()

    due_today = []
    due_next_3 = []
    due_next_week = []
    other_tasks = []

    for chore in chores:
        # Only process chores with a defined frequency
        if not chore.frequency:
            continue

        # If there is no last_completed value, treat this chore as due today.
        if not chore.last_completed:
            due_date_date = today_date
            last_completed_str = "Never"
        else:
            last_completed_local = chore.last_completed.replace(tzinfo=pytz.utc).astimezone(timezone)
            # If the chore was completed today, skip it (already done).
            if last_completed_local.date() == today_date:
                continue
            due_date = last_completed_local + chore.frequency
            last_completed_str = last_completed_local.strftime("%Y-%m-%d %H:%M:%S %Z")
            due_date_date = due_date.date()

        # Determine who completed it last.
        if chore.assigned_to:
            user_obj = User.query.get(chore.assigned_to)
            last_completed_by = user_obj.username if user_obj else "Unknown"
        else:
            last_completed_by = "N/A"

        # Prepare the chore dictionary.
        chore_dict = {
            'id': chore.id,
            'name': chore.name,
            'description': chore.description,
            'last_completed': last_completed_str,
            'last_completed_by': last_completed_by,
            'due_date': "Today" if due_date_date == today_date else due_date_date.strftime("%Y-%m-%d")
        }

        # Categorize based on the due_date.
        if due_date_date == today_date:
            due_today.append(chore_dict)
        elif today_date < due_date_date <= today_date + timedelta(days=3):
            due_next_3.append(chore_dict)
        elif today_date + timedelta(days=3) < due_date_date <= today_date + timedelta(days=7):
            due_next_week.append(chore_dict)
        else:
            other_tasks.append(chore_dict)

    return render_template('dashboard.html', users=users,
                           due_today=due_today,
                           due_next_3=due_next_3,
                           due_next_week=due_next_week,
                           other_tasks=other_tasks,
                           timezone=tz_name)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Define a list of common time zones for simplicity.
    common_timezones = [
        "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
        "Europe/London", "Europe/Paris", "Asia/Tokyo"
    ]
    if request.method == 'POST':
        selected_tz = request.form.get('timezone')
        if selected_tz in pytz.all_timezones:
            session['timezone'] = selected_tz
        return redirect(url_for('dashboard'))
    current_tz = session.get('timezone', 'UTC')
    return render_template('settings.html', timezones=common_timezones, current_tz=current_tz)

@app.route('/complete_chore', methods=['POST'])
def complete_chore():
    chore_id = request.form.get('chore_id')
    user_id = request.form.get('user_id')
    chore = Chore.query.get(chore_id)
    if chore:
        chore.last_completed = datetime.utcnow()
        chore.assigned_to = user_id
        db.session.commit()
        notif = Notification(user_id=user_id, chore_id=chore.id,
                             message=f"You completed '{chore.name}' on {chore.last_completed.strftime('%Y-%m-%d %H:%M:%S')}")
        db.session.add(notif)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_chore', methods=['GET', 'POST'])
def add_chore():
    if request.method == 'POST':
        household_id = request.form.get('household_id')
        name = request.form.get('name')
        description = request.form.get('description')
        frequency_input = request.form.get('frequency')
        try:
            # Convert the provided frequency (in days) to a timedelta object.
            frequency_interval = timedelta(days=int(frequency_input))
        except Exception:
            frequency_interval = None
        new_chore = Chore(
            household_id=household_id,
            name=name,
            description=description,
            frequency=frequency_interval,
            last_completed=None
        )
        db.session.add(new_chore)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        households = Household.query.all()
        return render_template('add_chore.html', households=households)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        household_id = request.form.get('household_id')
        username = request.form.get('username')
        email = request.form.get('email')
        new_user = User(household_id=household_id, username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        households = Household.query.all()
        return render_template('add_user.html', households=households)

@app.route('/manage_chores')
def manage_chores():
    # List all chores in a table
    chores = Chore.query.all()
    return render_template('manage_chores.html', chores=chores)

@app.route('/edit_chore/<int:chore_id>', methods=['GET', 'POST'])
def edit_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    if request.method == 'POST':
        chore.name = request.form.get('name')
        chore.description = request.form.get('description')
        frequency_input = request.form.get('frequency')
        try:
            chore.frequency = timedelta(days=int(frequency_input))
        except Exception:
            chore.frequency = None
        db.session.commit()
        return redirect(url_for('manage_chores'))
    return render_template('edit_chore.html', chore=chore)

@app.route('/delete_chore/<int:chore_id>', methods=['POST'])
def delete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    db.session.delete(chore)
    db.session.commit()
    return redirect(url_for('manage_chores'))

@app.route('/manage_users')
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.household_id = request.form.get('household_id')
        db.session.commit()
        return redirect(url_for('manage_users'))
    households = Household.query.all()
    return render_template('edit_user.html', user=user, households=households)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_users'))

# Initial setup CLI command
@app.cli.command("setup")
def setup():
    """
    Perform initial setup:
    - Create a default household, user, and a few chores if none exist.
    Run with: flask setup
    """
    if Household.query.first():
        print("Initial setup already completed.")
        return

    # Create default household
    household = Household(name="Default Household")
    db.session.add(household)
    db.session.commit()

    # Create default user
    user = User(household_id=household.id, username="admin", email="admin@example.com")
    db.session.add(user)
    db.session.commit()

    # Create default chores
    chore1 = Chore(
        household_id=household.id,
        name="Clean Kitchen",
        description="Clean all surfaces and mop the floor.",
        frequency=timedelta(days=1),
        assigned_to=user.id
    )
    chore2 = Chore(
        household_id=household.id,
        name="Do Laundry",
        description="Wash, dry, and fold clothes.",
        frequency=timedelta(days=2),
        assigned_to=user.id
    )
    db.session.add_all([chore1, chore2])
    db.session.commit()

    print("Initial setup completed: Default household, user, and chores created.")

if __name__ == '__main__':
    app.run(debug=True)
