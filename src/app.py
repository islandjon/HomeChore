from models import db, Household, User, Chore, Notification, ChoreCompletion
from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pytz
import os
import calendar

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql://postgres:postgres@0.0.0.0:5432/choredb')
app.secret_key = os.environ.get(
    'SECRET_KEY', 'default-secret-key')  # Needed for sessions

# Import the models from models.py

# Initialize the database with the app
db.init_app(app)

# Initialize the migration engine
migrate = Migrate(app, db)

@app.template_filter('localtime')
def localtime_filter(dt):
    if not dt:
        return "Never"
    # Get the user's timezone from the session (default to UTC)
    tz_name = session.get('timezone', 'UTC')
    timezone = pytz.timezone(tz_name)
    # Convert dt (assumed to be UTC) to the selected timezone
    local_dt = dt.replace(tzinfo=pytz.utc).astimezone(timezone)
    # Return a formatted string in Day Month format
    return local_dt.strftime("%a %b %d, %I:%M %p")

def calculate_next_due_date(last_date, due_days):
    """
    Given last_date (a date object) and due_days (a comma-separated string like "Mon,Wed,Fri"),
    returns the next date (after last_date) whose weekday is in due_days.
    """
    due_day_list = [day.strip() for day in due_days.split(',')]
    # Mapping of weekday abbreviations to numbers (Monday=0, Sunday=6)
    weekday_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    due_weekdays = [weekday_map[day] for day in due_day_list if day in weekday_map]

    for days_ahead in range(1, 8):  # Check the next 7 days
        next_date = last_date + timedelta(days=days_ahead)
        if next_date.weekday() in due_weekdays:
            return next_date
    return last_date  # fallback


@app.route('/')
def dashboard():
    tz_name = session.get('timezone', 'UTC')
    timezone = pytz.timezone(tz_name)
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(timezone)
    today_date = now.date()
    today_day = now.strftime("%a")  # e.g. "Mon", "Tue", etc.

    users = User.query.order_by(User.birthdate.asc()).all()
    user_chores = {}

    for user in users:
        # Get chores assigned to this user and sort them alphabetically.
        assigned_chores = sorted(user.assigned_chores, key=lambda c: c.name.lower())
        due_today = []
        other_tasks = []

        for chore in assigned_chores:
            
            if chore.assigned_to:
                user_obj = User.query.get(chore.assigned_to)
                chore.last_completed_by = user_obj.username if user_obj else "Unknown"
            else:
                chore.last_completed_by = "N/A"
            
            # Determine the next available date based on the cooldown.
            if chore.last_completed:
                last_completed_date = chore.last_completed.date()
                cooldown_days = chore.cooldown if chore.cooldown is not None else 1
                next_available_date = last_completed_date + timedelta(days=cooldown_days)
            else:
                # If never completed, it's available immediately.
                next_available_date = today_date

            # If today is before the next available date, skip this chore.
            if today_date < next_available_date:
                continue

            # Categorize the chore based on its due_days setting.
            if chore.due_days:
                # Split due_days into a list, trimming whitespace.
                due_day_list = [d.strip() for d in chore.due_days.split(',')]
                if today_day in due_day_list:
                    due_today.append(chore)
                else:
                    other_tasks.append(chore)
            else:
                # If no due_days are set, default to due today.
                due_today.append(chore)
            

        user_chores[user.id] = {
            'user': user,
            'due_today': due_today,
            'other_tasks': other_tasks
        }

    return render_template('dashboard.html', user_chores=user_chores, timezone=tz_name)



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


@app.route('/add_chore', methods=['GET', 'POST'])
def add_chore():
    if request.method == 'POST':
        household_id = request.form.get('household_id')
        name = request.form.get('name')
        description = request.form.get('description')
        due_days = request.form.getlist('due_days')
        due_days_str = ",".join([day.strip() for day in due_days]) if due_days else None
        cooldown_input = request.form.get('cooldown')
        try:
            cooldown_val = int(cooldown_input)
        except Exception:
            cooldown_val = 1  # default to 1 day if conversion fails

        selected_assignee_ids = request.form.getlist('assignees')
        # Update many-to-many relationship: assign allowed users.
        assignees = User.query.filter(User.id.in_(selected_assignee_ids)).all()

        new_chore = Chore(
            household_id=household_id,
            name=name,
            description=description,
            due_days=due_days_str,
            cooldown=cooldown_val,
            last_completed=None,
            assignees=assignees
        )
        db.session.add(new_chore)
        db.session.commit()
        return redirect(url_for('manage_chores'))
    else:
        households = Household.query.all()
        users = User.query.all()  # Fetch all users for the multi-select list.
        # Sort users by birthdate and then by username
        users = sorted(users, key=lambda u: (u.birthdate, u.username))
        return render_template('add_chore.html', households=households, users=users)


def get_next_assignee(chore):
    """
    Given a chore, determine the next assignee among its assignees:
    Return the user who has never completed the chore or who did it longest ago.
    """
    # Get the list of users assigned to this chore
    assignees = chore.assignees
    next_assignee = None
    oldest_completion = None
    
    for user in assignees:
        # Get the most recent completion for this chore by this user
        completion = (ChoreCompletion.query
                      .filter_by(chore_id=chore.id, user_id=user.id)
                      .order_by(ChoreCompletion.completed_at.desc())
                      .first())
        if completion is None:
            # If the user has never completed the chore, return immediately.
            return user
        else:
            if oldest_completion is None or completion.completed_at < oldest_completion:
                oldest_completion = completion.completed_at
                next_assignee = user
    return next_assignee

@app.route('/complete_chore', methods=['POST'])
def complete_chore():
    chore_id = request.form.get('chore_id')
    user_id = request.form.get('user_id')  # Ensure this is captured
    chore = Chore.query.get(chore_id)

    if chore and user_id:
        chore.last_completed = datetime.utcnow()
        chore.assigned_to = int(user_id)  # Assign to the selected user
        db.session.commit()

        # Log completion in ChoreCompletion table
        completion = ChoreCompletion(chore_id=chore.id, user_id=int(user_id))
        db.session.add(completion)
        db.session.commit()

        # Add a notification
        notification = Notification(
            user_id=int(user_id),
            chore_id=chore.id,
            message=f"You completed '{chore.name}' on {chore.last_completed.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        db.session.add(notification)
        db.session.commit()

    return redirect(url_for('dashboard'))



@app.route('/manage_chores')
def manage_chores():
    # List all chores in a table
    chores = Chore.query.all()
    # Sort chores by household and then by name
    chores = sorted(chores, key=lambda c: (c.name))
    return render_template('manage_chores.html', chores=chores)


@app.route('/edit_chore/<int:chore_id>', methods=['GET', 'POST'])
def edit_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    users = User.query.all()  # Fetch all users for the multi-select list.
    # Sort users by birthdate and then by username
    users = sorted(users, key=lambda u: (u.birthdate, u.username))
    if request.method == 'POST':
        # Your existing update logic
        chore.name = request.form.get('name')
        chore.description = request.form.get('description')
        due_days = request.form.getlist('due_days')
        chore.due_days = ",".join([day.strip() for day in due_days]) if due_days else None
        # Process allowed assignees from multi-select
        selected_assignee_ids = request.form.getlist('assignees')
        # Update many-to-many relationship: assign allowed users.
        chore.assignees = User.query.filter(User.id.in_(selected_assignee_ids)).all()
        cooldown_input = request.form.get('cooldown')
        try:
            chore.cooldown = int(cooldown_input)
        except Exception:
            chore.cooldown = 1
        db.session.commit()
        return redirect(url_for('manage_chores'))
    if request.args.get('ajax'):
        return render_template('edit_chore_form.html', chore=chore, users=users)
    else:
        return render_template('edit_chore.html', chore=chore, users=users)



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


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        birthdate = request.form.get('birthdate')
        household_id = request.form.get('household_id')
        color = request.form.get('color', '#3498db')  # Default blue
        avatar_file = request.files.get('avatar')

        # Convert birthdate string to date format
        birthdate = datetime.strptime(birthdate, "%Y-%m-%d").date() if birthdate else None

        # Handle avatar upload
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(app.static_folder, 'avatars', filename)
            avatar_file.save(avatar_path)
        else:
            filename = "default_avatar.png"

        new_user = User(username=username, email=email, birthdate=birthdate,
                        household_id=household_id, color=color, avatar=filename)
        db.session.add(new_user)
        db.session.commit()

        # Assign selected chores
        selected_chores = request.form.getlist('chores')
        new_user.assigned_chores = Chore.query.filter(Chore.id.in_(selected_chores)).all()
        db.session.commit()

        return redirect(url_for('dashboard'))

    households = Household.query.all()
    chores = Chore.query.all()
    return render_template('add_user.html', households=households, chores=chores)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.household_id = request.form.get('household_id')
        user.color = request.form.get('color', '#3498db')

        birthdate = request.form.get('birthdate')
        user.birthdate = datetime.strptime(birthdate, "%Y-%m-%d").date() if birthdate else None

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(app.static_folder, 'avatars', filename)
            avatar_file.save(avatar_path)
            user.avatar = filename  # Update avatar only if a new file is uploaded

        # Update chore assignments
        selected_chores = request.form.getlist('chores')
        user.assigned_chores = Chore.query.filter(Chore.id.in_(selected_chores)).all()

        db.session.commit()
        return redirect(url_for('dashboard'))

    households = Household.query.all()
    chores = Chore.query.all()
    return render_template('edit_user.html', user=user, households=households, chores=chores)


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
    user = User(household_id=household.id,
                username="admin", email="admin@example.com")
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
