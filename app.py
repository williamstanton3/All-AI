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
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{dbfile}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Getting the database object handle from the app
db = SQLAlchemy(app)

# Prepare and connect the LoginManager to this app
login_manager = LoginManager()
login_manager.init_app(app)

# function name of the route that has the login form (so it can redirect users)
login_manager.login_view = 'get_login' # type: ignore
login_manager.session_protection = "strong"

# function that takes a user id and as a string and returns that user
@login_manager.user_loader
def load_user(uid: str) -> User|None:
    return get_user(uid=int(uid))

# define a helper function that loads uses based on id or email
def get_user(uid: int|None = None, email: str|None = None) -> User|None:
    query: Select[Tuple[User]] = db.select(User)
    if   uid is not None: query = query.filter_by(id=uid)
    elif email is not None: query = query.filter_by(email=email)
    row:  Row[Tuple[User]]|None = db.session.execute(query).first()
    user: User|None = None if row is None else row[0]
    return user


# DATABASE SETUP

# Create a database model for Users
class User(UserMixin, db.Model):
    id:       Mapped[int]   = mapped_column(primary_key=True)
    email:    Mapped[str]   = mapped_column(nullable=False)
    pwd_hash: Mapped[bytes] = mapped_column(nullable=False)

    # make a write-only password property that just updates the stored hash
    @property
    def password(self):
        raise AttributeError("password is a write-only attribute")
    @password.setter
    def password(self, pwd: str) -> None:
        self.pwd_hash = pwd_hasher.hash(pwd)
    
    # add a verify_password convenience method
    def verify_password(self, pwd: str) -> bool:
        return pwd_hasher.check(pwd, self.pwd_hash)


with app.app_context():
    db.create_all() 

@app.get('/register/')
def get_register():
    form = RegisterForm()
    return render_template('register.html', form=form)

@app.post('/register/')
def post_register():
    form = RegisterForm()
    if form.validate():
        # check if there is already a user with this email address
        user: User|None = get_user(email=form.email.data)
        # if the email address is free, create a new user and send to login
        if user is None:
            user = User(email=form.email.data, password=form.password.data) # type:ignore
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('home'))
        else: # if the user already exists
            # flash a warning message and redirect to get registration form
            flash('There is already an account with that email address')
            return redirect(url_for('get_register'))
    else: # if the form was invalid
        # flash error messages and redirect to get registration form again
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
        # try to get the user associated with this email address
        user: User|None = get_user(email=form.email.data)
        # if this user exists and the password matches
        if user is not None and user.verify_password(str(form.password.data)):
            # log this user in through the login_manager
            login_user(user)
            # redirect the user to the page they wanted or the home page
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('home')
            return redirect(next)
        else: # if the user does not exist or the password is incorrect
            # flash an error message and redirect to login form
            flash('Invalid email address or password')
            return redirect(url_for('get_login'))
    else: # if the form was invalid
        # flash error messages and redirect to get login form again
        for field, error in form.errors.items():
            flash(f"{field}: {error}")
        return redirect(url_for('get_login'))
    
@app.get('/account')
def account():
    return render_template('account.html', current_user=current_user)

@app.get('/home')
def home():
    return render_template('home.html', current_user=current_user)

# redirect the user to the login page when they first access the site
@app.get('/')
def default_route():
    return redirect(url_for('get_login'))

@app.post("/api/chatgpt")
def chatgpt():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    app.logger.info("Chat endpoint called; model=%s prompt_len=%d", model, len(prompt))

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120,
            top_p=1.0,
            n=1,
            stop=["\n\n"],
        )

        # Extract reply defensively
        reply = None
        try:
            reply = completion.choices[0].message.content
        except Exception:
            try:
                reply = completion["choices"][0]["message"]["content"]
            except Exception:
                reply = None

        if not reply:
            app.logger.error("No text reply found in OpenAI response")
            return jsonify({"error": "No reply from model"}), 500

        return jsonify({"reply": reply})
    except Exception as e:
        app.logger.exception("OpenAI request failed")
        return jsonify({"error": str(e)}), 500



# # -------------------
# # Run app
# # -------------------
# if __name__ == "__main__":
#     app.run(debug=True)
