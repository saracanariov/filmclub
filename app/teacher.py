from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import func
import random
import functools

from . import db
from .models import User, Quiz, Question, Category, Choice, QuizQuestion, QuestionCategory, StudentAnswer

bp = Blueprint('teacher', __name__)

def teacher_required(view):
    """View decorator that requires a teacher user."""
    @functools.wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if not current_user.is_teacher():
            flash('You must be a teacher to access this page.')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/dashboard')
@teacher_required
def dashboard():
    """Teacher dashboard showing quizzes, questions, and categories."""
    quizzes = Quiz.query.filter_by(created_by=current_user.user_id).all()
    questions_count = Question.query.count()
    categories = Category.query.all()
    students = User.query.filter_by(role='student').all()
    
    return render_template('teacher/dashboard.html', 
                          quizzes=quizzes, 
                          questions_count=questions_count,
                          categories=categories,
                          students=students)

# User Management
@bp.route('/users')
@teacher_required
def list_users():
    """List all users (students)."""
    students = User.query.filter_by(role='student').all()
    return render_template('teacher/users.html', students=students)

@bp.route('/users/create', methods=('GET', 'POST'))
@teacher_required
def create_user():
    """Create a new student user."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
            
        if error is None:
            user = User(username=username, password=password, role='student')
            db.session.add(user)
            db.session.commit()
            flash(f"Student {username} created successfully.")
            return redirect(url_for('teacher.list_users'))
            
        flash(error)
    
    return render_template('teacher/create_user.html')

@bp.route('/users/<int:user_id>/delete', methods=('POST',))
@teacher_required
def delete_user(user_id):
    """Delete a student user."""
    user = User.query.get_or_404(user_id)
    if user.role != 'student':
        flash("You can only delete student accounts.")
        return redirect(url_for('teacher.list_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f"Student {user.username} deleted successfully.")
    return redirect(url_for('teacher.list_users'))

# Category Management
@bp.route('/categories')
@teacher_required
def list_categories():
    """List all categories."""
    categories = Category.query.all()
    return render_template('teacher/categories.html', categories=categories)

@bp.route('/categories/create', methods=('GET', 'POST'))
@teacher_required
def create_category():
    """Create a new category."""
    if request.method == 'POST':
        category_name = request.form['category_name']
        
        error = None
        if not category_name:
            error = 'Category name is required.'
        elif Category.query.filter_by(category_name=category_name).first() is not None:
            error = f"Category {category_name} already exists."
            
        if error is None:
            category = Category(category_name=category_name)
            db.session.add(category)
            db.session.commit()
            flash(f"Category {category_name} created successfully.")
            return redirect(url_for('teacher.list_categories'))
            
        flash(error)
    
    return render_template('teacher/create_category.html')

@bp.route('/categories/<int:category_id>/edit', methods=('GET', 'POST'))
@teacher_required
def edit_category(category_id):
    """Edit a category."""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category_name = request.form['category_name']
        
        error = None
        if not category_name:
            error = 'Category name is required.'
        elif (Category.query.filter_by(category_name=category_name).first() is not None and 
              category_name != category.category_name):
            error = f"Category {category_name} already exists."
            
        if error is None:
            category.category_name = category_name
            db.session.commit()
            flash(f"Category updated successfully.")
            return redirect(url_for('teacher.list_categories'))
            
        flash(error)
    
    return render_template('teacher/edit_category.html', category=category)

@bp.route('/categories/<int:category_id>/delete', methods=('POST',))
@teacher_required
def delete_category(category_id):
    """Delete a category."""
    category = Category.query.get_or_404(category_id)
    
    db.session.delete(category)
    db.session.commit()
    flash(f"Category {category.category_name} deleted successfully.")
    return redirect(url_for('teacher.list_categories'))

# Question Management
@bp.route('/questions')
@teacher_required
def list_questions():
    """List all questions."""
    questions = Question.query.all()
    return render_template('teacher/questions.html', questions=questions)

@bp.route('/questions/create', methods=('GET', 'POST'))
@teacher_required
def create_question():
    """Create a new question."""
    categories = Category.query.all()
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        difficulty = request.form['difficulty']
        category_ids = request.form.getlist('categories')
        
        # Get choices
        choice_texts = request.form.getlist('choice_text')
        is_correct_values = request.form.getlist('is_correct')
        
        error = None
        if not question_text:
            error = 'Question text is required.'
        elif not choice_texts or len(choice_texts) < 2:
            error = 'At least two choices are required.'
        elif not is_correct_values:
            error = 'At least one correct answer must be selected.'
            
        if error is None:
            # Create question
            question = Question(question_text=question_text, difficulty=difficulty)
            db.session.add(question)
            db.session.flush()  # Get question_id
            
            # Add categories
            for category_id in category_ids:
                category = Category.query.get(category_id)
                if category:
                    question.categories.append(category)
            
            # Add choices
            for i, choice_text in enumerate(choice_texts):
                if choice_text:  # Skip empty choices
                    is_correct = str(i) in is_correct_values
                    choice = Choice(
                        question_id=question.question_id,
                        choice_text=choice_text,
                        is_correct=is_correct
                    )
                    db.session.add(choice)
            
            db.session.commit()
            flash("Question created successfully.")
            return redirect(url_for('teacher.list_questions'))
            
        flash(error)
    
    return render_template('teacher/create_question.html', categories=categories)

@bp.route('/questions/<int:question_id>/edit', methods=('GET', 'POST'))
@teacher_required
def edit_question(question_id):
    """Edit a question."""
    question = Question.query.get_or_404(question_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        difficulty = request.form['difficulty']
        category_ids = request.form.getlist('categories')
        
        # Get choices
        choice_ids = request.form.getlist('choice_id')
        choice_texts = request.form.getlist('choice_text')
        is_correct_values = request.form.getlist('is_correct')
        
        error = None
        if not question_text:
            error = 'Question text is required.'
        elif not choice_texts or len(choice_texts) < 2:
            error = 'At least two choices are required.'
        elif not is_correct_values:
            error = 'At least one correct answer must be selected.'
            
        if error is None:
            # Update question
            question.question_text = question_text
            question.difficulty = difficulty
            
            # Update categories
            question.categories = []
            for category_id in category_ids:
                category = Category.query.get(category_id)
                if category:
                    question.categories.append(category)
            
            # Delete existing choices
            for choice in question.choices:
                db.session.delete(choice)
            
            # Add new choices
            for i, choice_text in enumerate(choice_texts):
                if choice_text:  # Skip empty choices
                    is_correct = str(i) in is_correct_values
                    choice = Choice(
                        question_id=question.question_id,
                        choice_text=choice_text,
                        is_correct=is_correct
                    )
                    db.session.add(choice)
            
            db.session.commit()
            flash("Question updated successfully.")
            return redirect(url_for('teacher.list_questions'))
            
        flash(error)
    
    return render_template('teacher/edit_question.html', question=question, categories=categories)

@bp.route('/questions/<int:question_id>/delete', methods=('POST',))
@teacher_required
def delete_question(question_id):
    """Delete a question."""
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully.")
    return redirect(url_for('teacher.list_questions'))

# Quiz Management
@bp.route('/quizzes')
@teacher_required
def list_quizzes():
    """List all quizzes."""
    quizzes = Quiz.query.filter_by(created_by=current_user.user_id).all()
    return render_template('teacher/quizzes.html', quizzes=quizzes)

@bp.route('/quizzes/create', methods=('GET', 'POST'))
@teacher_required
def create_quiz():
    """Create a new quiz."""
    categories = Category.query.all()
    
    if request.method == 'POST':
        title = request.form['title']
        question_count = int(request.form['question_count'])
        difficulty = request.form.get('difficulty', 'Any').strip()
        category_ids = request.form.getlist('categories')
        selection_method = request.form.get('selection_method', 'random').strip().lower()
        
        error = None
        if not title:
            error = 'Title is required.'
        elif question_count < 1:
            error = 'Question count must be at least 1.'
            
        if error is None:
            # Create quiz
            quiz = Quiz(
                title=title,
                question_count=question_count,
                difficulty=difficulty,
                created_by=current_user.user_id
            )
            db.session.add(quiz)
            db.session.flush()  # Get quiz_id
            
            # Add questions based on selection method
            if selection_method == 'random':
                # Build query for questions
                query = Question.query
                
                # Filter by categories if any are selected
                if category_ids:
                    # Convert to integers
                    category_ids = [int(cid) for cid in category_ids]
                    
                    # Use a subquery to find questions with matching categories
                    question_ids = db.session.query(QuestionCategory.question_id)\
                        .filter(QuestionCategory.category_id.in_(category_ids))\
                        .distinct().subquery()
                    
                    query = query.filter(Question.question_id.in_(question_ids))
                
                # Filter by difficulty if specified and not 'any'
                if difficulty.lower() != 'any':
                    query = query.filter(func.lower(Question.difficulty) == difficulty.lower())
                
                # Get all matching questions
                available_questions = query.all()
                
                # Only try to select questions if there are any available
                if available_questions:
                    # Randomly select questions up to the question_count
                    sample_size = min(question_count, len(available_questions))
                    if sample_size > 0:
                        selected_questions = random.sample(available_questions, sample_size)
                        
                        # Add selected questions to the quiz
                        for question in selected_questions:
                            quiz.questions.append(question)
                    else:
                        flash("No questions were added. Please add questions manually.")
                else:
                    flash("No questions matched your criteria. Please add questions manually.")
            
            db.session.commit()
            flash("Quiz created successfully.")
            return redirect(url_for('teacher.list_quizzes'))
            
        flash(error)
    
    return render_template('teacher/create_quiz.html', categories=categories)

@bp.route('/quizzes/<int:quiz_id>/view')
@teacher_required
def view_quiz(quiz_id):
    """View a quiz and its questions."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to view this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    return render_template('teacher/view_quiz.html', quiz=quiz)

@bp.route('/quizzes/<int:quiz_id>/edit', methods=('GET', 'POST'))
@teacher_required
def edit_quiz(quiz_id):
    """Edit a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to edit this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    categories = Category.query.all()
    
    if request.method == 'POST':
        title = request.form['title']
        question_count = int(request.form['question_count'])
        difficulty = request.form['difficulty']
        
        error = None
        if not title:
            error = 'Title is required.'
        elif question_count < 1:
            error = 'Question count must be at least 1.'
            
        if error is None:
            # Update quiz
            quiz.title = title
            quiz.question_count = question_count
            quiz.difficulty = difficulty
            
            db.session.commit()
            flash("Quiz updated successfully.")
            return redirect(url_for('teacher.list_quizzes'))
            
        flash(error)
    
    return render_template('teacher/edit_quiz.html', quiz=quiz, categories=categories)

@bp.route('/quizzes/<int:quiz_id>/delete', methods=('POST',))
@teacher_required
def delete_quiz(quiz_id):
    """Delete a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to delete this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully.")
    return redirect(url_for('teacher.list_quizzes'))

# Quiz Session Management
@bp.route('/quizzes/<int:quiz_id>/start', methods=('POST',))
@teacher_required
def start_quiz(quiz_id):
    """Start a quiz session."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to start this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Deactivate all other quizzes
    Quiz.query.filter_by(is_active=True).update({'is_active': False})
    
    # Activate this quiz
    quiz.is_active = True
    db.session.commit()
    
    flash(f"Quiz '{quiz.title}' is now active.")
    return redirect(url_for('teacher.quiz_session', quiz_id=quiz_id))

@bp.route('/quizzes/<int:quiz_id>/session')
@teacher_required
def quiz_session(quiz_id):
    """Control the quiz session."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to control this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Get all questions for this quiz
    questions = quiz.questions
    
    return render_template('teacher/quiz_session.html', quiz=quiz, questions=questions)

@bp.route('/quizzes/<int:quiz_id>/end', methods=('POST',))
@teacher_required
def end_quiz(quiz_id):
    """End a quiz session."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to end this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Deactivate the quiz
    quiz.is_active = False
    db.session.commit()
    
    flash(f"Quiz '{quiz.title}' has been deactivated.")
    return redirect(url_for('teacher.quiz_results', quiz_id=quiz_id))

@bp.route('/quizzes/<int:quiz_id>/results')
@teacher_required
def quiz_results(quiz_id):
    """View quiz results."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to view these results.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Get all students who participated in this specific quiz
    student_results = db.session.query(
        User.user_id,
        User.username,
        func.count(StudentAnswer.sa_id).label('total_answers'),
        func.sum(StudentAnswer.is_correct.cast(db.Integer)).label('correct_answers')
    ).join(
        StudentAnswer, User.user_id == StudentAnswer.student_id
    ).filter(
        StudentAnswer.quiz_id == quiz_id,
        User.role == 'student'
    ).group_by(
        User.user_id
    ).all()
    
    return render_template('teacher/quiz_results.html', quiz=quiz, student_results=student_results)

@bp.route('/quizzes/<int:quiz_id>/questions/add', methods=('GET', 'POST'))
@teacher_required
def add_questions_to_quiz(quiz_id):
    """Add questions to a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to edit this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Get questions not already in the quiz
    existing_question_ids = [q.question_id for q in quiz.questions]
    available_questions = Question.query.filter(~Question.question_id.in_(existing_question_ids) if existing_question_ids else True).all()
    categories = Category.query.all()
    
    if request.method == 'POST':
        question_ids = request.form.getlist('question_ids')
        
        if not question_ids:
            flash("Please select at least one question to add.")
        else:
            # Add selected questions to the quiz
            for question_id in question_ids:
                question = Question.query.get(question_id)
                if question:
                    quiz.questions.append(question)
            
            db.session.commit()
            flash(f"{len(question_ids)} question(s) added to the quiz successfully.")
            return redirect(url_for('teacher.view_quiz', quiz_id=quiz_id))
    
    return render_template('teacher/add_questions.html', quiz=quiz, available_questions=available_questions, categories=categories)

@bp.route('/quizzes/<int:quiz_id>/questions/<int:question_id>/remove', methods=('POST',))
@teacher_required
def remove_question_from_quiz(quiz_id, question_id):
    """Remove a question from a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)
    
    # Check if the quiz belongs to the current user
    if quiz.created_by != current_user.user_id:
        flash("You don't have permission to edit this quiz.")
        return redirect(url_for('teacher.list_quizzes'))
    
    # Remove the question from the quiz
    if question in quiz.questions:
        quiz.questions.remove(question)
        db.session.commit()
        flash("Question removed from the quiz successfully.")
    else:
        flash("This question is not part of the quiz.")
    
    return redirect(url_for('teacher.view_quiz', quiz_id=quiz_id))
