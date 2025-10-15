import flask
import flask_sqlalchemy
import flask_login
import datetime
from flask import request

app = flask.Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class Users(db.Model):
    email = db.Column(db.String(32), unique=True)
    username = db.Column(db.String(16), nullable=False, primary_key=True)
    password = db.Column(db.String(16), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    comments = db.relationship('Comments', backref='author', lazy='dynamic')

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    comments = db.relationship('Comments', backref='post', lazy='dynamic')

    author_username = db.Column(db.String(16), db.ForeignKey('users.username'), nullable=False)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)

    author_username = db.Column(db.String(16), db.ForeignKey('users.username'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

class CurrentUser(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in Users.query.value("username"):
        return
    user = CurrentUser()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')

    if username not in Users.query.value("username"):
        return

    user = CurrentUser()
    user.username = username
    return user

@app.route('/')
def index():
    return flask.render_template('index.html', post_list=Posts.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

    return flask.render_template('login.html', TITLE='Giriş yap')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if len(username) > 1 and len(email) > 1 and len(password) > 1 and password == password2:
            u = Users()
            u.username = username
            u.email = email
            u.password = password
            u.register_date = datetime.datetime.now()
            db.session.add(u)
            db.session.commit()
    return flask.render_template('register.html', TITLE='Kayıt ol')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)