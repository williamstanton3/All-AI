from __future__ import annotations
import os
from flask import Flask, render_template, url_for, redirect
from flask import request, session, flash, jsonify, current_app
from typing import Sequence, Tuple
from sqlalchemy import Row, Select
from datetime import datetime

from flask_login import LoginManager, login_required
from flask_login import login_user, logout_user, current_user

# Refactored modules
import modules.extensions as extensions
from modules.database_classes import User, ChatThread, ChatHistory
import modules.ai_endpoints as ai_endpoints

from loginforms import RegisterForm, LoginForm

# Identify necessary files
scriptdir = os.path.dirname(os.path.abspath(__file__))
dbfile = os.path.join(scriptdir, "users.sqlite3")
pepfile = os.path.join(scriptdir, "pepper.bin")

with open(pepfile, 'rb') as fin:
    pepper_key = fin.read()

# configure the flask application
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = 'correcthorsebatterystaple'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{dbfile}?timeout=10000"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize refactored extensions (sets extensions.db, extensions.client, extensions.pwd_hasher)
extensions.init_extensions(os.getenv("OPENAI_API_KEY"), os.getenv("GEMINI_API_KEY"), os.getenv("GROK_API_KEY"), os.getenv("CLAUDE_API_KEY"), os.getenv("DEEPSEEK_API_KEY"), pepper_key, app)

# Prepare and connect the LoginManager to this app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'get_login' # type: ignore
login_manager.session_protection = "strong"

# function that takes a user id as a string and returns that user
@login_manager.user_loader
def load_user(uid: str) -> User|None:
    return get_user(uid=int(uid))

# define a helper function that loads users based on id or email
def get_user(uid: int|None = None, email: str|None = None) -> User|None:
    query: Select[Tuple[User]] = extensions.db.select(User)
    if uid is not None:
        query = query.filter_by(id=uid)
    elif email is not None:
        query = query.filter_by(email=email)
    row: Row[Tuple[User]]|None = extensions.db.session.execute(query).first()
    user: User|None = None if row is None else row[0]
    return user

with app.app_context():
    extensions.db.create_all()

# -----------------------
# ROUTES
# -----------------------

@app.post('/api/chatgpt')
@login_required
def chatgpt():
    return ai_endpoints.gpt()

@app.post('/api/gemini')
@login_required
def gemini():
    return ai_endpoints.gemini()

@app.post('/api/claude')
@login_required
def claude():
    return ai_endpoints.claude()

@app.post('/api/falcon')
@login_required
def bard():
    return ai_endpoints.falcon()

@app.post('/api/bert')
@login_required
def llama():
    return ai_endpoints.bert()

@app.post('/api/mistral')
@login_required
def mistral():
    return ai_endpoints.mistral()

@app.post('/api/grok')
@login_required
def grok():
    return ai_endpoints.grok()

@app.post('/api/deepseek')
@login_required
def deepseek():
    return ai_endpoints.deepseek()

@app.get('/register/')
def get_register():
    form = RegisterForm()
    return render_template('register.html', form=form)

@app.post('/register/')
def post_register():
    form = RegisterForm()
    if form.validate():
        user: User|None = get_user(email=form.email.data)
        if user is None:
            statusBox = "Free"
            if form.status.data:
                statusBox = "Premium"
            user = User(email=form.email.data, password=form.password.data, status=statusBox) # type: ignore
            extensions.db.session.add(user)
            extensions.db.session.commit()
            return redirect(url_for('home'))
        else:
            flash('There is already an account with that email address')
            return redirect(url_for('get_register'))
    else:
        for field, error in form.errors.items():
            flash(f"{error}")
        return redirect(url_for('get_register'))

@app.get('/login/')
def get_login():
    form = LoginForm()
    return render_template('login.html', form=form)

@app.post('/login/')
def post_login():
    form = LoginForm()
    if form.validate():
        session.pop('current_thread_id', None) # Make a new thread upon login
        user: User|None = get_user(email=form.email.data)
        if user is not None and user.verify_password(str(form.password.data)):
            login_user(user)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('home')
            return redirect(next_page)
        else:
            flash('Invalid email address or password')
            return redirect(url_for('get_login'))
    else:
        for field, error in form.errors.items():
            flash(f"{field}: {error}")
        return redirect(url_for('get_login'))

@app.get('/account')
@login_required
def account():
    return render_template('account.html', current_user=current_user)

@app.get('/home')
@login_required
def home():
    # Clears current thread to make a new one when refreshing home page
    if 'current_thread_id' in session:
        session.pop('current_thread_id')
    # Gets all the threads with a SQL Alchemy query
    current_threads = (
        extensions.db.session.query(ChatThread)
        .filter_by(user_id=current_user.id)
        .order_by(ChatThread.date_created.desc())
        .all()
    )
    return render_template('home.html', current_user=current_user, threads=current_threads)

@app.get('/')
def default_route():
    return redirect(url_for('get_login'))

@app.post('/api/new_thread')
@login_required
def new_thread():
    session.pop('current_thread_id', None) # Remove current thread from session
    return jsonify({"status": "new thread created"}), 200

@app.get('/api/thread/<int:thread_id>')
@login_required
def switch_thread(thread_id: int):
    # sets current threadID to one that was clicked
    session['current_thread_id']= thread_id

    # SQL call to get ALL history entries
    history_entries= ChatHistory.query.filter_by(thread_id=thread_id).order_by(ChatHistory.id).all()

    history = [
        {
            "user_input": entry.user_input,
            "model_name": entry.model_name,
            "model_response": entry.model_response,
            "date_saved": entry.date_saved.strftime('%Y-%m-%d %H:%M:%S')
        }
        for entry in history_entries
    ]

    return jsonify({"history": history})