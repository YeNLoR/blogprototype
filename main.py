import datetime
import flask
from flask import request
import flask_sqlalchemy
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
from utils import check_password, process_content, get_tag_list, search_parser

app = flask.Flask(__name__)

app.config['SECRET_KEY'] = 'LFFV3RFHLDl'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

moderators = [1]

class Users(db.Model, flask_login.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False)
    password = db.Column(db.String, nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    comments = db.relationship('Comments', backref='author', lazy='dynamic')

post_tag_relation = db.Table('post_tag_relation',
                             db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
                             db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))

class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(48))

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    comments = db.relationship('Comments', backref='post', lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.relationship('Tags', secondary=post_tag_relation, backref=db.backref('posts'))

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
        else:
            return f"Yanlış kullanıcı adı yada şifre. <a href='{request.referrer}'>Geri git</a>"

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
        if len(username) > 0 and check_password(password) and password == password2:
            u = Users()
            u.username = username
            u.password = generate_password_hash(password)
            u.register_date = datetime.datetime.now()
            db.session.add(u)
            db.session.commit()
            return flask.redirect(flask.url_for('login'))
        else:
            return f"Şifre en az 8 en fazla 16 karakter içermelidir ve A-Z, a-z, 0-9, _, - harici karakterler kullanılmamalıdır. <a href='{request.referrer}'>Geri git</a>"
    return flask.render_template('register.html',
                                 TITLE='Kayıt ol')

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
        if check_password_hash(user.password, password) and check_password(new_password):
            user.password = generate_password_hash(new_password)
            db.session.add(user)
            db.session.commit()
        else:
            return f"Şifre en az 8 en fazla 16 karakter içermelidir ve A-Z, a-z, 0-9, _, - harici karakterler kullanılmamalıdır  <a href='{request.referrer}'>Geri git</a>"

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
        tags = get_tag_list(request.form['tags'])
        final_content = process_content(content)
        if len(final_content) > 0 and len(title) > 0:
            new_post = Posts()
            new_post.title = title
            new_post.content = final_content
            new_post.date_posted = datetime.datetime.now()
            new_post.author_id = flask_login.current_user.id
            for tag in tags:
                if not db.session.query(Tags).filter_by(name=tag).all():
                    db.session.add(Tags(name=str(tag)))
                new_post.tags.append(db.session.query(Tags).filter_by(name=str(tag)).first())
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
    if request.method == 'POST':
        comment = request.form['comment']
        author_id = flask_login.current_user.id
        new_comment = Comments()
        new_comment.author_id = author_id
        new_comment.post_id = post_id
        new_comment.content = comment
        new_comment.date_posted = datetime.datetime.now()
        db.session.add(new_comment)
        db.session.commit()
        return flask.redirect(request.referrer)
    else:
        return flask.render_template('show_post.html',
                                     post=check_post,
                                     comments=check_post.comments)

@app.route("/edit/<post_id>", methods=['GET','POST'])
@flask_login.login_required
def edit_post(post_id):
    check_post = db.session.query(Posts).filter_by(id=post_id).first()
    old_tags = {
        db.session.query(Tags).filter_by(id=tag.id).first().name
        for tag in check_post.tags
    }
    tag_string = ""
    for tag in old_tags:
        tag_string += f"{tag},"
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = get_tag_list(request.form['tags'])
        final_content = process_content(content)
        if len(final_content) > 0 and len(title) > 0:
            check_post.title = title
            check_post.content = final_content
            check_post.tags = []
            for tag in tags:
                if not db.session.query(Tags).filter_by(name=tag).all():
                    db.session.add(Tags(name=str(tag)))
                check_post.tags.append(db.session.query(Tags).filter_by(name=str(tag)).first())

            db.session.commit()
    return flask.render_template('edit.html',
                                 post=check_post,
                                 tags=tag_string)



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_dict = search_parser(request.form['search'])
        user_string = search_dict.get('user', None)
        post_string = search_dict.get('post', None)
        tag_string = search_dict.get('tags', None)
        posts = db.session.query(Posts)
        if user_string == None and post_string == None and tag_string == None:
            posts = posts.filter(Posts.title.contains(request.form['search'])).all()
        else:
            if user_string and user_string != '':
                posts = posts.join(Posts.author).filter(Users.username.contains(user_string)).all()
            if post_string and post_string != '':
                posts = posts.filter(Posts.title.contains(post_string))
            if tag_string and tag_string != '':
                posts = posts.filter(Posts.tags.any(Tags.name.contains(tag_string)))
        return  flask.render_template('index.html',
                                      posts=posts)
    return f"Hata <a href='{flask.url_for('index')}'>Ana sayfaya dön.</a>"

@app.route("/delete_post", methods=['POST'])
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
        post_to_delete.comments.delete(synchronize_session='fetch')
        db.session.delete(post_to_delete)
        db.session.commit()
        return flask.redirect(flask.url_for('index'))
    return f"Diğer kullanıcıların paylaşımlarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

@app.route("/delete_user", methods=['POST'])
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
        user.comments.delete(synchronize_session='fetch')
        user.posts.delete(synchronize_session='fetch')
        db.session.delete(user)
        db.session.commit()
        return flask.redirect(request.referrer)
    return f"Diğer kullanıcıların hesaplarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

@app.route("/delete_comment", methods=['POST'])
@flask_login.login_required
def delete_comment():
    comment_to_delete = {}
    moderator = False
    print(request.form)
    if request.form["delete_comment"]:
        comment_id = int(request.form["delete_comment"])
        comment_to_delete = db.session.query(Comments).filter_by(id=comment_id).first()
        print(comment_to_delete)
    if flask_login.current_user.id in moderators:
        moderator = True
    if moderator or comment_to_delete.author_id == flask_login.current_user.id:
        db.session.delete(comment_to_delete)
        db.session.commit()
        return flask.redirect(request.referrer)
    return f"Diğer kullanıcıların yorumlarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not db.session.query(Users).filter(Users.username == 'admin').first():
            mod = Users()
            mod.username = "admin"
            mod.password = generate_password_hash("admin")
            mod.register_date = datetime.datetime.now()
            db.session.add(mod)
            db.session.commit()
    app.run(host="0.0.0.0", debug=True)