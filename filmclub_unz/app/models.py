from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='creator', lazy=True)
    answers = db.relationship('StudentAnswer', backref='student', lazy=True)
    
    def __init__(self, username, password, role):
        self.username = username
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.user_id)
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    quiz_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    question_count = db.Column(db.Integer, default=10)
    difficulty = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', secondary='quiz_questions', lazy='subquery',
                               backref=db.backref('quizzes', lazy=True))
    
    def __init__(self, title, question_count, difficulty, created_by):
        self.title = title
        self.question_count = question_count
        self.difficulty = difficulty
        self.created_by = created_by
        self.is_active = False

class Category(db.Model):
    __tablename__ = 'categories'
    
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __init__(self, category_name):
        self.category_name = category_name

class Question(db.Model):
    __tablename__ = 'questions'
    
    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_text = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    choices = db.relationship('Choice', backref='question', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', secondary='question_categories', lazy='subquery',
                                backref=db.backref('questions', lazy=True))
    
    def __init__(self, question_text, difficulty=None):
        self.question_text = question_text
        self.difficulty = difficulty

# Join table for quiz-question many-to-many relationship
class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    qq_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('quiz_id', 'question_id', name='uq_quiz_question'),)

# Join table for question-category many-to-many relationship
class QuestionCategory(db.Model):
    __tablename__ = 'question_categories'
    
    qc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('question_id', 'category_id', name='uq_question_category'),)

class Choice(db.Model):
    __tablename__ = 'choices'
    
    choice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    choice_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    def __init__(self, question_id, choice_text, is_correct=False):
        self.question_id = question_id
        self.choice_text = choice_text
        self.is_correct = is_correct

class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'
    
    sa_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey('choices.choice_id', ondelete='CASCADE'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id', ondelete='CASCADE'), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question')
    choice = db.relationship('Choice')
    quiz = db.relationship('Quiz')
    
    # Updated constraint: ensures a student can answer the same question in different quizzes
    __table_args__ = (db.UniqueConstraint('student_id', 'question_id', 'quiz_id', name='uq_student_question_quiz'),)
    
    def __init__(self, student_id, question_id, choice_id, quiz_id):
        self.student_id = student_id
        self.question_id = question_id
        self.choice_id = choice_id
        self.quiz_id = quiz_id
        # Check if the choice is correct
        choice = Choice.query.get(choice_id)
        if choice:
            self.is_correct = choice.is_correct