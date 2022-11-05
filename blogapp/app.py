from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, LoginManager, UserMixin, logout_user, login_required
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///' + os.path.join(base_dir,'blog.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = '7cdac6f34660280097af437ebae1de'


db = SQLAlchemy(app)
login_manager = LoginManager(app)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(), nullable=False, unique=True)
    gender = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)
    blogpost = db.relationship('Blogpost', backref='user')
    

    def __repr__(self):
        return f"User <{self.username}>"
    
@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))  


class Blogpost(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=True)
    author = db.Column(db.String(30), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    date_created = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Blogpost <{self.author}>"


class Contact(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    message = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"Contact <{self.name}>"
 


@app.route('/')
def index():
    posts = Blogpost.query.order_by(Blogpost.date_created.desc()).all()

    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        username = request.form.get('username')
        gender = request.form.get('gender')
        email = request.form.get('email')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirmpassword')

        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('register')) 

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        new_user = User(first_name=first_name, last_name=last_name, username=username, gender=gender, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET','POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first() 

    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('index'))

    return render_template('signin.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
@login_required
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        contact_form = Contact(name=name, email=email, message=message)
        db.session.add(contact_form)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('contact.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/blog/<int:blog_id>/')
def blog(blog_id):
    blog = Blogpost.query.get(blog_id)
    return render_template('blog.html', blog=blog, current_user=current_user)


@app.route('/addpost', methods=['GET','POST'])
@login_required
def addpost():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        content = request.form.get('content')

        post = Blogpost(title=title, author=author, content=content, user_id=current_user.id, date_created=datetime.now())
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('post.html')


@app.route('/edit/<int:blog_id>', methods=['GET','POST'])
@login_required
def edit(blog_id):
    blog_to_update = Blogpost.query.get_or_404(blog_id)


    if request.method == 'POST':
        blog_to_update.title = request.form.get('title')
        blog_to_update.content = request.form.get('content')


        db.session.commit()

        return redirect(url_for('blog', blog_id=blog_to_update.id))

    return render_template('edit.html', blog=blog_to_update, title=Blogpost.title, content=Blogpost.content)


@app.route('/delete/<int:blog_id>/', methods=['GET'])
@login_required
def delete_blog(blog_id):
    blog_to_delete = Blogpost.query.get_or_404(blog_id)

    db.session.delete(blog_to_delete)
    db.session.commit()

    return redirect(url_for('index'))




if __name__=='__main__':
    app.run(debug=True)
