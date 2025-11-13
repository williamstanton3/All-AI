from __future__ import annotations
import os
from flask import Flask, render_template, url_for, redirect
from flask import request, session, flash, jsonify
from openai import OpenAI

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from typing import Sequence, Tuple
from sqlalchemy import Row, Select

from flask_login import UserMixin, LoginManager, login_required
from flask_login import login_user, logout_user, current_user

# Import from local package files
from hashing_examples import UpdatedHasher
from loginforms import RegisterForm, LoginForm

from datetime import datetime

# Identify necessary files
scriptdir = os.path.dirname(os.path.abspath(__file__))
dbfile = os.path.join(scriptdir, "users.sqlite3")
pepfile = os.path.join(scriptdir, "pepper.bin")

with open(pepfile, 'rb') as fin:
    pepper_key = fin.read() 

# create a new instance of UpdatedHasher using that pepper key 
pwd_hasher = UpdatedHasher(pepper_key)

# configure the flask application 
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = 'correcthorsebatterystaple'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{dbfile}?timeout=10000"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Getting the database object handle from the app
db = SQLAlchemy(app)

# Prepare and connect the LoginManager to this app
login_manager = LoginManager()
login_manager.init_app(app)

# function name of the route that has the login form (so it can redirect users)
login_manager.login_view = 'get_login' # type: ignore
login_manager.session_protection = "strong"

# function that takes a user id as a string and returns that user
@login_manager.user_loader
def load_user(uid: str) -> User|None:
    return get_user(uid=int(uid))

# define a helper function that loads users based on id or email
def get_user(uid: int|None = None, email: str|None = None) -> User|None:
    query: Select[Tuple[User]] = db.select(User)
    if uid is not None:
        query = query.filter_by(id=uid)
    elif email is not None:
        query = query.filter_by(email=email)
    row: Row[Tuple[User]]|None = db.session.execute(query).first()
    user: User|None = None if row is None else row[0]
    return user


# DATABASE SETUP

# Create a database model for Users
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False)
    pwd_hash: Mapped[bytes] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default='Free')  # Free or Premium
    
    # Relationship to ChatThread table
    threads: Mapped[list[ChatThread]] = db.relationship(back_populates='user')  # type: ignore

    @property
    def password(self):
        raise AttributeError("password is write-only")
    
    @password.setter
    def password(self, pwd: str) -> None:
        self.pwd_hash = pwd_hasher.hash(pwd)
    
    def verify_password(self, pwd: str) -> bool:
        return pwd_hasher.check(pwd, self.pwd_hash)

# Create a database model for a Chat Thread
class ChatThread(db.Model):
    __tablename__ = 'chat_threads'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    thread_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    date_created: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)
    
    # Relationship to User table
    user: Mapped[User] = db.relationship(back_populates='threads')  # type: ignore
    
    # Relationship to ChatHistory table
    messages: Mapped[list[ChatHistory]] = db.relationship(
        back_populates='thread', 
        cascade="all, delete-orphan", # Deletes responses if the thread is deleted
        order_by='ChatHistory.id' #orders chronologically by ID
    ) # type: ignore
    
# Create database model for chat history
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(db.ForeignKey('chat_threads.id'), nullable=False)
    
    user_input: Mapped[str] = mapped_column(db.Text, nullable=False)

    model_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    model_response: Mapped[str] = mapped_column(db.Text, nullable=False)
    date_saved: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)
    
    # Relationship to ChatThread table
    thread: Mapped[ChatThread] = db.relationship(back_populates='messages')  # type: ignore


with app.app_context():
    db.create_all()


# -----------------------
# ROUTES
# -----------------------

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
            db.session.add(user)
            db.session.commit()
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
def account():
    return render_template('account.html', current_user=current_user)

@app.get('/home')
def home():
    # Clears current thread to make a new one when refreshing home page
    if 'current_thread_id' in session:
        session.pop('current_thread_id') 
    # Gets all the threads with a SQL Alchemy query
    current_threads = ChatThread.query.filter_by(user_id=current_user.id).order_by(ChatThread.date_created.desc()).all() # type: ignore
    
    return render_template('home.html', current_user=current_user, threads=current_threads)

@app.get('/')
def default_route():
    return redirect(url_for('get_login'))


# -----------------------
# ChatGPT endpoint with conversation memory
# -----------------------
@app.post("/api/chatgpt")
def chatgpt():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    app.logger.info("Chat endpoint called; model=%s prompt_len=%d", model, len(prompt))

    # trie to get the current thread from the session (if any)
    thread_id= session.get('current_thread_id')
    current_thread= None
    
    if thread_id is not None:
        current_thread= db.session.get(ChatThread, thread_id)
    else:
        # Create a new thread for this conversation
        thread_title= prompt[:10] + ("..." if len(prompt) > 50 else "")
        current_thread= ChatThread(
            user_id= current_user.id, # type: ignore
            thread_name= thread_title # type: ignore
        )
        db.session.add(current_thread)
        db.session.commit()
        
        # Save the current thread ID in the session
        session['current_thread_id']= current_thread.id
        
    try:
        # Retrieve ALL chat history for the current thread
        thread_id= session.get('current_thread_id') #gets current thread id from session
        messages = [{"role": "system", "content": "asdfasdf"}] # Initial system message
        
        # If there is an existing thread, load its history
        if thread_id is not None:
            # gets LIMITED nubmber of chat history entries using a SQLAlchemy query
            history_entries = ChatHistory.query.filter_by(thread_id=thread_id).order_by(ChatHistory.id.desc()).limit(2).all()
            history_entries.reverse()  # Reverse to maintain chronological order
            
            for entry in history_entries:
                # Reconstruct the conversation sequence from the saved inputs and outputs
                messages.append({"role": "user", "content": entry.user_input})
                messages.append({"role": "assistant", "content": entry.model_response})
            
        

        messages.append({"role": "user", "content": prompt})

        # --- Call OpenAI API ---
        completion = client.chat.completions.create(
            model=model,
            messages=messages, # type: ignore
            temperature=0.2,
            max_tokens=120,
            top_p=1.0
        )

        reply = completion.choices[0].message.content

        # --- Save new message in database ---
        new_message = ChatHistory(
            thread_id= current_thread.id, # type: ignore
            user_input=prompt, # type: ignore
            model_name=model, # type: ignore
            model_response=reply # type: ignore
        ) 
        db.session.add(new_message)
        db.session.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        app.logger.exception("OpenAI request failed")
        return jsonify({"error": str(e)}), 500

@app.post('/api/new_thread')
def new_thread():
    session.pop('current_thread_id', None) # Remove current thread from session
    return jsonify({"status": "new thread created"}), 200 

# @app.get('/api/thread/<int:thread_id>')
# def switch_thread(thread_id: int):
    
    
# # -------------------
# # Run app
# # -------------------
# if __name__ == "__main__":
#     app.run(debug=True)
