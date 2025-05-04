from flask import Flask, render_template, request, redirect, url_for, session
from multiprocessing import Process
from sql_req import request as db_request

import os
import signal

app = Flask(__name__)
app.secret_key = os.urandom(24)  

connection = db_request()


def is_logged_in():
    return 'user' in session

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Страница входа (GET + POST)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # 💡 Здесь можешь добавить реальную проверку с базой
        if username == "admin" and password == "1234":
            session['user'] = {'name': username}
            return redirect(url_for('index'))
        else:
            error = "Неверный логин или пароль"
            return render_template("login.html", error=error)

    return render_template("login.html")  # форма логина

# Выход
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))  # Остаёмся на той же странице


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, use_reloader=False, debug=True)
