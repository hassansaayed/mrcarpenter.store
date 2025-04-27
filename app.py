from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # This ID is auto-generated
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)


# Initialize DB
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('home.html', user=user)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists!"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        new_comment = Comment(user_id=session['user_id'], content=content)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('forum'))

    comments = Comment.query.all()
    return render_template('forum.html', comments=comments)

@app.route('/forum/comment/<int:comment_id>')
def view_comment(comment_id):
    # This is where the IDOR vulnerability comes into play.
    # We're allowing users to access any comment if they know the comment ID.
    comment = Comment.query.get(comment_id)
    if comment:
        return f"Comment ID: {comment.id} <br> Content: {comment.content}"
    return "Comment not found.", 404

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        content = request.form['content']
        new_task = Task(content=content, user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
    
    # Retrieve all tasks for the logged-in user
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return render_template('todo.html', tasks=tasks)


@app.route('/todo/delete/<int:task_id>', methods=['GET'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    
    # IDOR vulnerability: we are not checking if the task belongs to the current user
    db.session.delete(task)
    db.session.commit()
    
    return redirect('/todo')


if __name__ == '__main__':
    app.run(debug=True)
