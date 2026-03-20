from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import *
from models import db, User, Progress, ChatHistory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from openai import OpenAI

app = Flask(__name__)
app.config.from_object("config")

db.init_app(app)

def create_admin():
    admin = User.query.filter_by(username="admin").first()

    if not admin:
        admin = User()
        admin.username = "admin"
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")

login_manager = LoginManager()
login_manager.init_app(app)

client = OpenAI(api_key="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")

# ---------------- LOAD USER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- COURSES ----------------
courses = ["Intro", "Firewall", "Encryption", "SQL Injection"]

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/tutor")
@login_required
def tutor():
    return render_template("tutor.html")

# ---------------- AI ----------------
@app.route("/ask", methods=["POST"])
@login_required
def ask():
    user_message = request.json["message"]

    progress = Progress.query.filter_by(user_id=current_user.id).first()
    if not progress:
        progress = Progress()
        progress.user_id = current_user.id
        progress.topic_index = 0
        db.session.add(progress)
        db.session.commit()

    topic = courses[progress.topic_index]

    response = client.chat.completions.create(
        model="gpt-4-mini",
        messages=[{"role": "user", "content": f"Teach {topic}: {user_message}"}]
    )

    reply = response.choices[0].message.content

    # Save chat
    chat = ChatHistory(user_id=current_user.id, message=f"[{topic}] {user_message}", reply=reply)
    db.session.add(chat)
    db.session.commit()

    return jsonify({"reply": reply, "topic": topic})

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)