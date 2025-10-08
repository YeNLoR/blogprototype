import flask
import sqlite3
from flask import request

app = flask.Flask(__name__)
with sqlite3.connect('users.db') as connect:
    cursor = connect.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
    connect.commit()
@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            return "<p>Merhaba admin</p>"
    return flask.render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        if len(username) > 1 and len(password) > 1 and password == password2:
            with sqlite3.connect('users.db') as connect:
                cursor = connect.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                               (username, password))

    return flask.render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)