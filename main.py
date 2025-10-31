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
    username = db.Column(db.String(16), nullable=False)
    password = db.Column(db.String, nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    comments = db.relationship('Comments', backref='author', lazy='dynamic')

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
    return db.session.query(Users).filter_by(id=user_id).first()

@app.context_processor
def inject_user_status():
    return dict(logged_in=flask_login.current_user.is_authenticated)
@app.route('/')
def index():
    latest_posts = db.session.query(Posts).order_by(Posts.date_posted.desc()).limit(24)
    return flask.render_template('index.html',
                                 TITLE = "Benim Ultra Mega Güzel Blog Prototipim",
                                 posts=latest_posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.query(Users).filter_by(username=username).first()
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
        password = request.form['password']
        password2 = request.form['password2']
        if len(username) > 1 and len(password) > 1 and password == password2:
            u = Users()
            u.username = username
            u.password = generate_password_hash(password)
            u.register_date = datetime.datetime.now()
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

@app.route('/profile/<profile_id>', methods=['GET','POST'])
def show_profile(profile_id):
    user = db.session.query(Users).filter_by(id=profile_id).first()
    posts_from_user = db.session.query(Posts).filter_by(author_id=user.id).all()
    return flask.render_template('profile.html',
                                TITLE="Profil",
                                user=user,
                                posts=posts_from_user)

@app.route('/post', methods=['GET','POST'])
@flask_login.login_required
def post():
    if request.method == 'POST' and "submit" in request.form:
        title = request.form['title']
        content = request.form['content']
        content = markdown.markdown(content)
        if len(content) > 0 and len(title) > 0:
            new_post = Posts()
            new_post.title = title
            new_post.content = content
            new_post.date_posted = datetime.datetime.now()
            new_post.author_id = flask_login.current_user.id
            db.session.add(new_post)
            db.session.commit()
            return flask.redirect(flask.url_for('index'))

    return flask.render_template('post.html',
                                 TITLE = 'Post Oluştur')

@app.route('/post/<post_id>', methods=['GET','POST'])
def show_post(post_id):
    check_post = db.session.query(Posts).filter_by(id=post_id).first()
    if check_post is None:
        flask.abort(404)
    else:
        return flask.render_template('show_post.html',
                                     post=check_post)
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_string = request.form['search']
        link = "/search/" + search_string
        return flask.redirect(link)
    return None


@app.route("/search/<search>")
def search_title(search_post):
    posts = db.session.query(Posts).filter(Posts.title.contains(search_post)).all()
    return flask.render_template('index.html',
                                 posts=posts)

@app.route("/delete_post/", methods=['POST'])
@flask_login.login_required
def delete_post():
    post_to_delete = {}
    moderator = False
    if request.form["delete_post"]:
        post_id = int(request.form["delete_post"])
        post_to_delete = db.session.query(Posts).filter_by(id=post_id).first()
    if flask_login.current_user.id in moderators:
        moderator = True
    if moderator or post_to_delete.author_id == flask_login.current_user.id:
        db.session.delete(post_to_delete)
        db.session.commit()
        return flask.redirect(request.referrer)
    return f"Diğer kullanıcıların paylaşımlarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

@app.route("/delete_user/", methods=['POST'])
@flask_login.login_required
def delete_user():
    user = {}
    moderator = False
    if request.form["delete_user"]:
        user_id = int(request.form["delete_user"])
        user = db.session.query(Users).filter_by(id=user_id).first()
    if flask_login.current_user.id in moderators:
        moderator = True
    if moderator or flask_login.current_user.id == user.id:
        db.session.delete(user)
        db.session.commit()
        return flask.redirect(request.referrer)
    return f"Diğer kullanıcıların hesaplarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True)