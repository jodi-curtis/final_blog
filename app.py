"""An educational example of a basic blog application using Flask and SQLAlchemy.

Note that we're using the simpler Legacy Query API in this example:
https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/legacy-query/
"""
from statistics import median, mean

from flask import Flask, flash, render_template, redirect, request, url_for
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from models import User, BlogPost, db
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object('config')  # Load configuration from config.py

login_manager = LoginManager(app)
login_manager.login_view = "login_page"

with app.app_context():
    db.init_app(app)
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allow_edit(post):
    return post.author == current_user


@app.route("/")
def index():
    return render_template("index.html", posts=BlogPost.query.all())


@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_action():
    username = request.form["username"]
    password = request.form["password"]
    if User.query.filter_by(username=username).first():
        flash(f"The username '{username}' is already taken")
        return redirect(url_for("register_page"))

    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash(f"Welcome {username}!")
    return redirect(url_for("index"))


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_action():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f"No such user '{username}'")
        return redirect(url_for("login_page"))
    if password != user.password:
        flash(f"Invalid password for the user '{username}'")
        return redirect(url_for("login_page"))

    login_user(user)
    flash(f"Welcome back, {username}!")
    return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
@login_required
def logout_page():
    return render_template("logout.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout_action():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for("index"))  # TODO: Fix the 'next' functionality


@app.route("/create", methods=["GET"])
@login_required
def create_post_page():
    return render_template("create.html")


@app.route("/create", methods=["POST"])
@login_required
def create_post_action():
    post = BlogPost(
        title=request.form["title"],
        content=request.form["content"],
        author=current_user,
    )
    db.session.add(post)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>")
def post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template("post.html", post=post, allow_edit=allow_edit(post))


@app.route("/edit/<int:post_id>", methods=["GET"])
@login_required
def edit_page(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if not allow_edit(post):
        flash(f"Only this post's author ({post.author}) is allowed to edit it")
        return redirect(url_for("post", post_id=post.id))

    return render_template("edit.html", post=post)


@app.route("/edit/<int:post_id>", methods=["POST"])
@login_required
def edit_action(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if not allow_edit(post):
        flash(f"Only this post's author ({post.author}) is allowed to edit it")
        return redirect(url_for("post", post_id=post.id))

    post.title = request.form["title"]
    post.content = request.form["content"]
    db.session.commit()
    return redirect(url_for("post", post_id=post.id))


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_action(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if not allow_edit(post):
        flash(f"Only this post's author ({post.author}) is allowed to delete it")
        return redirect(url_for("post", post_id=post.id))
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    post_lengths = BlogPost.get_post_lengths()

    if post_lengths:
        return render_template(
            "stats.html",
            posts_exist=True,
            average_length=mean(post_lengths),
            median_length=median(post_lengths),
            max_length=max(post_lengths),
            min_length=min(post_lengths),
            total_length=sum(post_lengths),
        )
    else:
        return render_template("stats.html", posts_exist=False)


if __name__ == "__main__":
    app.run(debug=True)
