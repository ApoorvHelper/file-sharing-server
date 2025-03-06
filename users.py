from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

users_bp = Blueprint('users', __name__, template_folder='templates')

# In-memory "database" for users: {username: {"password": hashed_password, "role": role}}
# WARNING: This "database" resets every time the server restarts.
users_db = {}

@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'User')  # Default role is "User"
        if username in users_db:
            flash("Username already exists. Please choose a different one.", "warning")
            return redirect(url_for('users.register'))
        # Updated: Use 'pbkdf2:sha256' as the hash method.
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users_db[username] = {"password": hashed_password, "role": role}
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('users.login'))
    return render_template('register.html')

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_db.get(username)
        if user and check_password_hash(user["password"], password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user["role"]
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for('users.login'))
    return render_template('login.html')

@users_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('users.login'))
