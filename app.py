from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, session
import os
import datetime
import json
from functools import wraps
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong random secret key
Bootstrap(app)

UPLOAD_FOLDER = 'shared'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Files to store metadata and users persistently
METADATA_FILE = 'file_metadata.json'
USERS_FILE = 'users.json'

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# Global users database loaded from file.
users_db = load_users()

# Login required decorator for protecting routes.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
         if not session.get('logged_in'):
             flash("Please log in first.", "warning")
             return redirect(url_for('login'))
         return f(*args, **kwargs)
    return decorated_function

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users_db:
            flash("Username already exists. Please choose a different one.", "warning")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        # Default role is "User"
        users_db[username] = {"password": hashed_password, "role": "User"}
        save_users(users_db)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route that checks the users_db
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_db.get(username)
        if user and check_password_hash(user["password"], password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user.get("role", "User")
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Home route with file metadata and search functionality.
@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').lower()
    metadata = load_metadata()
    files = []
    for f in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            mod_time = os.path.getmtime(filepath)
            mod_date = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            if search_query in f.lower():
                uploader = metadata.get(f, {}).get('uploader', 'Unknown')
                upload_time = metadata.get(f, {}).get('upload_time', mod_date)
                files.append({
                    'name': f,
                    'size': size,
                    'mod_date': mod_date,
                    'uploader': uploader,
                    'upload_time': upload_time
                })
    return render_template('index.html', files=files, search_query=search_query)

# File upload route that records uploader and upload time.
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "warning")
        return redirect(url_for('index'))
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Record metadata about uploader and upload time.
    metadata = load_metadata()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    metadata[filename] = {
        'uploader': session.get('username', 'Unknown'),
        'upload_time': current_time
    }
    save_metadata(metadata)

    flash("File uploaded successfully", "success")
    return redirect(url_for('index'))

# File download route.
@app.route('/files/<filename>')
@login_required
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# File deletion route (also removes metadata).
@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
        metadata = load_metadata()
        if filename in metadata:
            del metadata[filename]
            save_metadata(metadata)
        flash(f"{filename} deleted successfully", "success")
    else:
        flash("File not found", "danger")
    return redirect(url_for('index'))

# Custom error pages.
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, message="Page Not Found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, message="Internal Server Error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
