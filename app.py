from __future__ import annotations
import os
from flask import Flask, render_template, url_for, redirect
from flask import request, session, flash, jsonify, current_app
from typing import Sequence, Tuple
from sqlalchemy import Row, Select
from datetime import datetime

from flask_login import LoginManager, login_required
from flask_login import login_user, logout_user, current_user

import modules.extensions as extensions
from modules.dbms import User, ChatThread, ChatHistory
import modules.ai_endpoints as ai_endpoints

from loginforms import RegisterForm, LoginForm

scriptdir = os.path.dirname(os.path.abspath(__file__))
dbfile = os.path.join(scriptdir, "users.sqlite3")
pepfile = os.path.join(scriptdir, "pepper.bin")

with open(pepfile, 'rb') as fin:
    pepper_key = fin.read()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = 'correcthorsebatterystaple'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{dbfile}?timeout=10000"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

extensions.init_extensions(
    claude_model       = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307"),
    claude_key         = os.getenv("CLAUDE_API_KEY"),
    claude_max_tokens  = int(os.getenv("CLAUDE_MAX_TOKENS", "120")),
    claude_temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.2")),

    deepseek_model      = os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    deepseek_key        = os.getenv("DEEPSEEK_API_KEY"),
    deepseek_max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "120")),
    deepseek_temperature= float(os.getenv("DEEPSEEK_TEMPERATURE", "0.2")),

    gemini_model       = os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    gemini_key         = os.getenv("GEMINI_API_KEY"),
    gemini_max_tokens  = int(os.getenv("GEMINI_MAX_TOKENS", "120")),
    gemini_temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.2")),

    openai_model       = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    openai_key         = os.getenv("OPENAI_API_KEY"),
    openai_max_tokens  = int(os.getenv("OPENAI_MAX_TOKENS", "120")),
    openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2")),

    grok_model         = os.getenv("GROK_MODEL", "grok-3-mini"),
    grok_key           = os.getenv("GROK_API_KEY"),
    grok_max_tokens    = int(os.getenv("GROK_MAX_TOKENS", "120")),
    grok_temperature   = float(os.getenv("GROK_TEMPERATURE", "0.2")),

    mistral_model      = os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
    mistral_key        = os.getenv("MISTRAL_API_KEY"),
    mistral_max_tokens = int(os.getenv("MISTRAL_MAX_TOKENS", "120")),
    mistral_temperature= float(os.getenv("MISTRAL_TEMPERATURE", "0.2")),

    llama_model        = os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    llama_key          = os.getenv("LLAMA_API_KEY"),
    llama_max_tokens   = int(os.getenv("LLAMA_MAX_TOKENS", "120")),
    llama_temperature  = float(os.getenv("LLAMA_TEMPERATURE", "0.2")),

    qwen_model         = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-7B-Instruct-Turbo"),
    qwen_key           = os.getenv("QWEN_API_KEY"),
    qwen_max_tokens    = int(os.getenv("QWEN_MAX_TOKENS", "120")),
    qwen_temperature   = float(os.getenv("QWEN_TEMPERATURE", "0.2")),

    pepper=pepper_key,
    flask_app=app)

# Prepare and connect the LoginManager to this app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'get_login' # type: ignore
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(uid: str) -> User | None:
    return get_user(uid=int(uid))

def get_user(uid: int|None = None, email: str|None = None) -> User | None:
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

@app.post('/api/llama')
@login_required
def llama_together():
    return ai_endpoints.llama_together()

@app.post('/api/qwen')
@login_required
def qwen_together():
    return ai_endpoints.qwen_together()

@app.post('/api/ensure_thread')
@login_required
def ensure_thread():
    # make a new thread if there isn't currently one
    data = request.get_json()
    prompt = data.get('prompt', 'New Chat')
    current_models = set(data.get('models', []))
    if 'current_thread_id' in session:
        thread_id = session['current_thread_id']
        
        history_models = extensions.db.session.query(ChatHistory.model_name).filter_by(thread_id=thread_id).distinct().all()
        
        existing_models = {row[0] for row in history_models}
        if existing_models and existing_models != current_models:
            session.pop('current_thread_id', None)
        else:
            return jsonify({"status": "exists", "id": thread_id})
        
    
    # thread title
    thread_name = prompt[:15] + "..." if len(prompt) > 15 else prompt

    new_thread = ChatThread(
        user_id=current_user.id, #type:ignore
        thread_name=thread_name, #type:ignore
        date_created=datetime.now() #type:ignore
    )
    extensions.db.session.add(new_thread)
    extensions.db.session.commit()
    session['current_thread_id'] = new_thread.id
    
    
    return jsonify({
        "status": "created", 
        "id": new_thread.id,
        "name": new_thread.thread_name,
        "date": new_thread.date_created.strftime('%b %d %I:%M'),
        "models": ", ".join(sorted(current_models))
    })


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
            user = User(email=form.email.data, password=form.password.data, status="Free") # type: ignore
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

@app.post('/account/upgrade')
@login_required
def upgrade_account():
    # Update the user's status
    current_user.status = "Premium"
    extensions.db.session.commit()
    
    # Optional: Add a flash message
    flash("Successfully upgraded to Premium!")
    
    return redirect(url_for('account'))

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
    for thread in current_threads:

        models = extensions.db.session.query(ChatHistory.model_name)\
            .filter_by(thread_id=thread.id)\
            .distinct().all()
        
        # Convert list of rows [('CHATGPT',), ('GEMINI',)] -> "CHATGPT, GEMINI"
        valid_models = [m[0] for m in models if m[0]] # Filter out None
        thread.display_models = ", ".join(sorted(valid_models))
        
    return render_template('home.html', current_user=current_user, threads=current_threads)

@app.get('/')
def default_route():
    return redirect(url_for('get_login'))

@app.post('/api/new_thread')
@login_required
def new_thread():
    session.pop('current_thread_id', None)
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


@app.delete('/api/thread/<int:thread_id>')
@login_required
def delete_thread(thread_id):
    thread = extensions.db.session.query(ChatThread).filter_by(id=thread_id, user_id=current_user.id).first()
    
    if not thread:
        return jsonify({"error": "Thread not found or access denied"}), 403

    extensions.db.session.query(ChatHistory).filter_by(thread_id=thread_id).delete()
    extensions.db.session.delete(thread)
    extensions.db.session.commit()
    
    if session.get('current_thread_id') == thread_id:
        session.pop('current_thread_id', None)

    return jsonify({"status": "deleted"})