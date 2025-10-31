import markdown
import flask
import flask_sqlalchemy
import flask_login
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request


app = flask.Flask(__name__)

app.config['SECRET_KEY'] = 'LFFV3RFHLDl'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class Users(db.Model, flask_login.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(32), unique=True)
    username = db.Column(db.String(16), nullable=False)
    password = db.Column(db.String, nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    comments = db.relationship('Comments', backref='author', lazy='dynamic')

    def get_id(self):
        return str(self.id)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    #tags = db.Column(db.String(64), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    comments = db.relationship('Comments', backref='post', lazy='dynamic')
    author_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)

    author_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(str(user_id))

@app.context_processor
def inject_user_status():
    return dict(logged_in=flask_login.current_user.is_authenticated)
@app.route('/')
def index():
    latest_posts = Posts.query.order_by(Posts.date_posted.desc()).limit(24)
    return flask.render_template('index.html',
                                 TITLE = "Benim Ultra Mega Güzel Blog Prototipim",
                                 posts=latest_posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            flask_login.login_user(user, remember=True)
            return flask.redirect(flask.url_for('profile'))

    return flask.render_template('login.html',
                                 TITLE='Giriş yap')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('index'))

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
            u.password = generate_password_hash(password)
            u.register_date = datetime.datetime.now()
            for key, value in u.__dict__.items():
                print(key, value, type(value))
            db.session.add(u)
            db.session.commit()
    return flask.render_template('register.html',
                                 TITLE='Kayıt ol')

moderators = [1, 2]

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def profile():
    if "new_username" in request.form:
        new_username = request.form['new_username']
        user = db.session.query(Users).filter_by(id=flask_login.current_user.id).first()
        user.username = new_username
        db.session.add(user)
        db.session.commit()

    if "new_password" in request.form:
        new_password = request.form['new_password']
        password = request.form['password']
        user = db.session.query(Users).filter_by(id=flask_login.current_user.id).first()
        if check_password_hash(user.password, password) and 16 >= len(new_password) >= 1:
            user.password = generate_password_hash(new_password)
            db.session.add(user)
            db.session.commit()

    return flask.render_template('profile.html',
                                 TITLE="Profil",
                                 user=flask_login.current_user,
                                 posts=Posts.query.filter_by(author_id=flask_login.current_user.id).order_by(Posts.date_posted.desc()).all(),
                                 admin=True
    )

@app.route('/profile/<id>', methods=['GET','POST'])
def show_profile(id):
    user = db.session.query(Users).filter_by(id=id).first()
    return flask.render_template('profile.html',
                                TITLE="Profil",
                                user=user,
                                posts=Posts.query.filter_by(author_id=id).all())

@app.route('/post', methods=['GET','POST'])
@flask_login.login_required
def post():
    if request.method == 'POST' and "submit" in request.form:
        title = request.form['title']
        content = request.form['content']
        content = markdown.markdown(content)
        if len(content) > 0 and len(title) > 0:
            post = Posts()
            post.title = title
            post.content = content
            post.date_posted = datetime.datetime.now()
            post.author_id = flask_login.current_user.id
            db.session.add(post)
            db.session.commit()
            return flask.redirect(flask.url_for('index'))

    return flask.render_template('post.html',
                                 TITLE = 'Post Oluştur')

@app.route('/post/<id>', methods=['GET','POST'])
def show_post(id):
    post = Posts.query.get(id)
    if post is None:
        flask.abort(404)
    else:
        return flask.render_template('show_post.html',
                                     post=post)
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search = request.form['search']
        link = "/search/" + search
        print(link)
        return flask.redirect(link)

@app.route("/search/<search>")
def search_title(search):
    posts = Posts.query.filter(Posts.title.contains(search)).all()
    return flask.render_template('index.html',
                                 posts=posts)
@app.route("/delete_post/", methods=['POST'])
@flask_login.login_required
def delete_post():
    post = {}
    moderator = False
    if request.form["delete_post"]:
        post_id = int(request.form["delete_post"])
        post = Posts.query.filter_by(id=post_id).first()
    if flask_login.current_user.id in moderators:
        moderator = True
    if moderator or post.author_id == flask_login.current_user.id:
        db.session.delete(post)
        db.session.commit()
        return flask.redirect(request.referrer)

@app.route("/delete_user/", methods=['POST'])
@flask_login.login_required
def delete_user():
    user = {}
    moderator = False
    if request.form["delete_user"]:
        user_id = int(request.form["delete_user"])
        user = Users.query.filter_by(id=user_id).first()
    print(user)
    if flask_login.current_user.id in moderators:
        moderator = True
    if moderator or flask_login.current_user.id == user.id:
        db.session.delete(user)
        db.session.commit()
        return flask.redirect(request.referrer)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)