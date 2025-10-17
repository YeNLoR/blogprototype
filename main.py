import uuid

import flask
import flask_sqlalchemy
import flask_login
import datetime
from flask import request

app = flask.Flask(__name__)

app.config['SECRET_KEY'] = 'LFFV3RFHLDl'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class Users(db.Model, flask_login.UserMixin):
    email = db.Column(db.String(32), unique=True)
    username = db.Column(db.String(16), nullable=False, primary_key=True)
    password = db.Column(db.String(16), nullable=False)
    salt = db.Column(db.String(16), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    comments = db.relationship('Comments', backref='author', lazy='dynamic')

    def get_id(self):
        return str(self.username)

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

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(str(user_id))

@app.route('/')
def index():
    return flask.render_template('index.html', post_list=Posts.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()
        if user and password == user.password:
            flask_login.login_user(user, remember=True)
            return flask.redirect(flask.url_for('profile'))

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
            u.salt = 1
            u.register_date = datetime.datetime.now()
            db.session.add(u)
            db.session.commit()
    return flask.render_template('register.html', TITLE='Kayıt ol')

@app.route('/profile')
@flask_login.login_required
def profile():
    return flask.render_template('profile.html',
                                 username=flask_login.current_user.username,
                                 posts=Posts.query.filter_by(author_username=flask_login.current_user.username).all())

@app.route('/post', methods=['GET','POST'])
@flask_login.login_required
def post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if len(content) > 0 and len(title) > 0:
            post = Posts()
            post.title = title
            post.content = content
            post.date_posted = datetime.datetime.now()
            post.author_username = flask_login.current_user.username
            db.session.add(post)
            db.session.commit()

    return flask.render_template('post.html', user=flask_login.current_user.username    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)