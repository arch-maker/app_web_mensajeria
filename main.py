import hashlib
import uuid

from flask import Flask, render_template, request, redirect, url_for, make_response
from models import User, db, Message

app = Flask(__name__)
db.create_all()


@app.route("/")
def index():
    token_session = request.cookies.get("token_session")

    if token_session:
        user = db.query(User).filter_by(token_session=token_session).first()

    else:
        user = None

    return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    hash_pass = hashlib.sha256(password.encode()).hexdigest()

    user = db.query(User).filter_by(email=email).first()

    if not user:
        user = User(name=name, email=email, password=hash_pass)

        db.add(user)
        db.commit()

    if hash_pass != user.password:
        return "Contraseña incorrecta! Introduzca la contraseña correcta!"

    elif hash_pass == user.password:

        token_session = str(uuid.uuid4())

        user.token_session = token_session
        db.add(user)
        db.commit()

        response = make_response(redirect(url_for('index')))
        response.set_cookie("token_session", token_session, httponly=True, samesite='Strict')

        return response


@app.route("/profile", methods=["GET"])
def profile():
    token_session = request.cookies.get("token_session")

    user = db.query(User).filter_by(token_session=token_session, delete=False).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    token_session = request.cookies.get("token_session")

    user = db.query(User).filter_by(token_session=token_session, delete=False).first()

    if request.method == "GET":
        if user:
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")

        if old_password and new_password:
            h_old_password = hashlib.sha256(old_password.encode()).hexdigest()
            h_new_password = hashlib.sha256(new_password.encode()).hexdigest()

            if h_old_password == user.password:
                user.password = h_new_password

            else:
                return "Operacion incorrecta! Su antigua contraseña no es correcta"

        user.name = name
        user.email = email

        db.add(user)
        db.commit()

        return redirect(url_for("profile"))


@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    token_session = request.cookies.get("token_session")

    user = db.query(User).filter_by(token_session=token_session, delete=False).first()

    if request.method == "GET":
        if user:
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        user.delete = True
        db.add(user)
        db.commit()

        return redirect(url_for("index"))


@app.route("/sobreapp", methods=["GET"])
def sobreapp():

    return render_template("sobreapp.html")


@app.route("/users", methods=["GET"])
def all_users():
    users = db.query(User).filter_by(delete=False).all()

    return render_template("users.html", users=users)


@app.route("/user/<user_id>", methods=["GET"])
def user_details(user_id):
    user = db.query(User).get(int(user_id))

    return render_template("user_details.html", user=user)


@app.route("/envio", methods=["GET"])
def envio():
    users = db.query(User).all()
    messages = db.query(Message).all()
    return render_template("envio.html", users=users, messages=messages)


@app.route("/send/", methods=["POST"])
def send_message():
    sender_id = request.form.get("sender_id", type=int)
    receiver_id = request.form.get("receiver_id", type=int)
    message = request.form.get("message", type=str)

    sender = db.query(User).filter_by(id=sender_id).first()
    receiver = db.query(User).filter_by(id=receiver_id).first()

    if sender and receiver and message:
        message = Message(message=message, sender=sender_id, receiver=receiver_id)
        db.add(message)
        db.commit()
    return redirect("/envio")


if __name__ == '__main__':
    app.run()