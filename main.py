from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy 


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


app.secret_key = 'keygenerated'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    body = db.Column(db.String(8000))

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner
    

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30))
    password = db.Column(db.String(30))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password



@app.before_request
def require_login():
   
    allowed_routes = ['login', 'list_blogs', 'index', 'signup']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/', methods=['GET'])
def index():
   
    all_the_users = User.query.all()

    return render_template('index.html', users=all_the_users)    

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username_as_entered_in_login_form = request.form['username']
        password_as_entered_in_login_form = request.form['password']
        user_exists_in_db = User.query.filter_by(username=username_as_entered_in_login_form).first()
        
        if user_exists_in_db:
            if user_exists_in_db.password == password_as_entered_in_login_form:
                
                session['username'] = username_as_entered_in_login_form
                
                flash('Logged in')
                return redirect('/newpost')
            
            else: 
                
                flash("Sorry, that's not your password. Try again, please.", 'error')
          
                return render_template('login.html', username=username_as_entered_in_login_form)

        
        else:
            
            flash("Please signed up.", 'error')
            return redirect('/signup')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    
    if request.method == 'POST':
        username_as_entered_in_signup_form = request.form['username']
        password_as_entered_in_signup_form = request.form['password']
        verify = request.form['verify']

        
        existing_user = User.query.filter_by(username=username_as_entered_in_signup_form).first()
        if existing_user:
            
            flash("This user name exists.", 'error')

            return redirect('/signup')
        
        else:
             
            if validate_input(username_as_entered_in_signup_form, password_as_entered_in_signup_form, verify) == True:

                new_user = User(username_as_entered_in_signup_form, password_as_entered_in_signup_form)
                db.session.add(new_user)
                db.session.flush()
                db.session.commit()
                
                session['username'] = username_as_entered_in_signup_form
            
                
                return redirect('/newpost')
            

    return render_template('signup.html')


def validate_input(username, password, verify):
    
    username_error = ""
    password_error = ""
    verify_error   = ""
    
    if len(username) == 0:
        username_error = "empty feild!"
    elif not 3 < len(username) <= 30:
        username_error = "Wrong entry"
        username = ''
    elif " " in username:
        username_error = "No space allowed"
        username = ''

    if len(password) == 0:
        password_error = "Please enter a password"
    elif not 3 <= len(password) <= 30:
        password_error = "wrong format"  
    elif " " in password:
        password_error = "no space allowed"

    if password != verify and not password_error:
        verify_error = "passwords do not match!"

    if not username_error and not password_error and not verify_error:
        return True
    else:
        if username_error:
            flash(username_error, 'error')
        elif password_error:
            flash(password_error, 'error')
        elif verify_error:
            flash(verify_error, 'error')
        return render_template('signup.html', username=username)  

@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():
        
    user_who_just_added_post = request.args.get("id")
    user_you_want = request.args.get("user_you_want")

    if user_who_just_added_post:
        blog = Blog.query.filter_by(id=user_who_just_added_post).first()
        return render_template("most_recent_single_post.html", blog=blog)

    elif user_you_want:
     
        blogs = Blog.query.filter_by(owner_id=user_you_want).all()
        author = User.query.filter_by(id=user_you_want).first()
        return render_template('all_posts_of_one_user.html', title="hmm", blogs=blogs, user=author)
    
    else:
        
        blogs = Blog.query.all()
        return render_template('list_of_all_blog_posts.html', title="Grr", blogs=blogs)

       

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    
    current_user_is_owner_of_blog_post = User.query.filter_by(username=session['username']).first()
  

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        
        if len(title) == 0 and len(body) == 0:
            flash("empty field", 'error')
            return render_template('create_new_post.html')        
        elif len(title) == 0:
            flash('Need to type a title', 'error')
            return render_template('create_new_post.html', body=body)
        elif len(body) == 0:
            flash('body empty', 'error')
            return render_template('create_new_post.html', title=title)

        else:
          
            new_entry = Blog(title, body, current_user_is_owner_of_blog_post)
            

            db.session.add(new_entry)
            db.session.flush()
            db.session.commit()

            newest_post = new_entry.id
            return redirect("/blog?id={0}".format(newest_post))

    return render_template('create_new_post.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

if __name__ == '__main__':
    app.run()