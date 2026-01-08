import datetime
import os
import json
from flask import Flask, request, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from utils import check_password, process_content, get_tag_list, search_parser, allowed_file

UPLOAD_FOLDER = 'static/content/user'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'LFFV3RFHLDl'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)
moderators = []

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False)
    password = db.Column(db.String, nullable=False)
    profile_pic_path = db.Column(db.String, default="/static/content/profile_picture/img.png", nullable=False)
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
    return dict(logged_in=current_user.is_authenticated, params=request.args)

def trigger_status(message, response=None, status_code=None, Header=None):
    status_html = render_template("status.html", message=message)
    if status_code is None:
        status_code = 200 if response else 204
    content = response if response else ''
    return content, status_code, {
        "HX-Trigger": json.dumps({
            "statusReport": {"content": status_html}
        })
    }

@app.route('/')
def index():
    latest_posts = db.session.query(Posts).order_by(Posts.date_posted.desc()).limit(24).all()
    return render_template('index.html',
                                 TITLE = "Mert'in blog sitesi",
                                 page=2,
                                 posts=latest_posts)

@app.route('/feed')
def feed():
    page = int(request.args.get("page",1))
    posts = db.session.query(Posts)
    if request.args.get("from_user"):
        user_id = request.args.get("from_user")
        user = db.session.get(Users, user_id)
        posts = user.posts
    ##
    if request.args.get("search",""):
        search_dict = search_parser(request.args.get('search',""))
        user_string = search_dict.get('user', "")
        post_string = search_dict.get('post', "")
        tag_string = search_dict.get('tags', "")
        posts = db.session.query(Posts)
        if not user_string and not post_string and not tag_string:
            posts = posts.filter(Posts.title.contains(request.args.get('search')))
        else:
            if user_string and user_string != '':
                posts = posts.join(Posts.author).filter(Users.username.contains(user_string))
            if post_string and post_string != '':
                posts = posts.filter(Posts.title.contains(post_string))
            if tag_string and tag_string != '':
                posts = posts.filter(Posts.tags.any(Tags.name.contains(tag_string)))
    ##
    posts = posts.order_by(Posts.date_posted.desc()).offset((page-1)*24).limit(24).all()
    if posts:
        return render_template('post_list.html',
                                     TITLE="Mert'in blog sitesi",
                                     page=page + 1,
                                     posts=posts)
    else:
        return 'post yok'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.query(Users).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('profile'))
        else:
            return f"Yanlış kullanıcı adı yada şifre. <a href='{request.referrer}'>Geri git</a>"

    return render_template('login.html',
                                 TITLE='Giriş yap')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

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
            return redirect(url_for('login'))
        else:
            return f"Şifre en az 8 en fazla 16 karakter içermelidir ve A-Z, a-z, 0-9, _, - harici karakterler kullanılmamalıdır. <a href='{request.referrer}'>Geri git</a>"
    return render_template('register.html',
                                 TITLE='Kayıt ol')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if "new_username" in request.form:
        new_username = request.form['new_username']
        user = db.session.query(Users).filter_by(id=current_user.id).first()
        user.username = new_username
        db.session.add(user)
        db.session.commit()

    if "new_password" in request.form:
        new_password = request.form['new_password']
        password = request.form['password']
        user = db.session.query(Users).filter_by(id=current_user.id).first()
        if check_password_hash(user.password, password) and check_password(new_password):
            user.password = generate_password_hash(new_password)
            db.session.add(user)
            db.session.commit()
        else:
            return f"Şifre en az 8 en fazla 16 karakter içermelidir ve A-Z, a-z, 0-9, _, - harici karakterler kullanılmamalıdır  <a href='{request.referrer}'>Geri git</a>"

    return render_template('profile.html',
                                 TITLE="Profil",
                                 user=current_user,
                                 from_user = current_user.id,
                                 posts=Posts.query.filter_by(author_id=current_user.id).order_by(Posts.date_posted.desc()).all(),
                                 admin=True,
                                 page=1
    )

@app.route('/profile/<profile_id>', methods=['GET','POST'])
def show_profile(profile_id):
    user = db.session.query(Users).filter_by(id=profile_id).first()
    posts_from_user = db.session.query(Posts).filter_by(author_id=user.id).all()
    return render_template('profile.html',
                                TITLE="Profil",
                                user=user,
                                from_user=profile_id,
                                posts=posts_from_user)

@app.route('/profilepicture', methods=['GET', 'POST'])
@login_required
def profile_picture():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = str(current_user.id) + '.jpg'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user = db.session.get(Users, current_user.id)
            user.profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            db.session.commit()
            return trigger_status("profil resmin değiştirildi")
    return ""

@app.route('/post', methods=['GET','POST'])
@login_required
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
            new_post.author_id = current_user.id
            for tag in tags:
                if not db.session.query(Tags).filter_by(name=tag).all():
                    db.session.add(Tags(name=str(tag)))
                new_post.tags.append(db.session.query(Tags).filter_by(name=str(tag)).first())
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('post.html',
                                 TITLE = 'Post Oluştur')

@app.route('/post/<post_id>', methods=['GET','POST'])
def show_post(post_id):
    check_post = db.session.query(Posts).filter_by(id=post_id).first()
    if check_post is None:
        return redirect(request.referrer)
    if request.method == 'POST':
        comment = request.form['comment']
        author_id = current_user.id
        new_comment = Comments()
        new_comment.author_id = author_id
        new_comment.post_id = post_id
        new_comment.content = comment
        new_comment.date_posted = datetime.datetime.now()
        db.session.add(new_comment)
        db.session.commit()
        return redirect(request.referrer)
    else:
        return render_template('show_post.html',
                                     post=check_post,
                                     comments=check_post.comments)

@app.route("/edit/<post_id>", methods=['GET','POST'])
@login_required
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
    return render_template('edit.html',
                                 post=check_post,
                                 tags=tag_string)

@app.route("/edit_comment" , methods=['GET','POST'])
@login_required
def edit_comment():
    if request.method == 'POST':
        id = request.form['id']
        content = request.form['edited_comment']
        current_user_id = current_user.id
        comment = db.session.query(Comments).filter_by(id=id).first()
        if comment.author_id == current_user_id:
            comment.content = content
            comment.date_posted = datetime.datetime.now()
            db.session.commit()
            return redirect(request.referrer)

@app.route("/delete_post", methods=['POST'])
@login_required
def delete_post():
    post_to_delete = {}
    moderator = False
    if request.form["delete_post"]:
        post_id = int(request.form["delete_post"])
        post_to_delete = db.session.query(Posts).filter_by(id=post_id).first()
    if current_user.id in moderators:
        moderator = True
    if moderator or post_to_delete.author_id == current_user.id:
        post_to_delete.comments.delete(synchronize_session='fetch')
        db.session.delete(post_to_delete)
        db.session.commit()
        return trigger_status("Post başarı ile silindi")
    return trigger_status("Diğer kullanıcıların paylaşımlarını silme yetkin yok.")

@app.route("/delete_user", methods=['POST'])
@login_required
def delete_user():
    user = {}
    moderator = False
    if request.form["delete_user"]:
        user_id = int(request.form["delete_user"])
        user = db.session.query(Users).filter_by(id=user_id).first()
    if current_user.id in moderators:
        moderator = True
    if moderator or current_user.id == user.id:
        user.comments.delete(synchronize_session='fetch')
        user.posts.delete(synchronize_session='fetch')
        db.session.delete(user)
        db.session.commit()
        return redirect(request.referrer)
    return f"Diğer kullanıcıların hesaplarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"

@app.route("/delete_comment", methods=['POST'])
@login_required
def delete_comment():
    comment_to_delete = {}
    moderator = False
    print(request.form)
    if request.form["delete_comment"]:
        comment_id = int(request.form["delete_comment"])
        comment_to_delete = db.session.query(Comments).filter_by(id=comment_id).first()
        print(comment_to_delete)
    if current_user.id in moderators:
        moderator = True
    if moderator or comment_to_delete.author_id == current_user.id:
        db.session.delete(comment_to_delete)
        db.session.commit()
        return redirect(request.referrer)
    return f"Diğer kullanıcıların yorumlarını silme yetkin yok. <a href='{request.referrer}'>Geri git</a>"


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)