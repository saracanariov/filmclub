from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import func
import functools

from . import db
from .models import User, Quiz, Question, Choice, QuizQuestion, StudentAnswer

bp = Blueprint('student', __name__)

def student_required(view):
    """View decorator that requires a student user."""
    @functools.wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if not current_user.is_student():
            flash('You must be a student to access this page.')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/dashboard')
@student_required
def dashboard():
    """Student dashboard showing active quizzes."""
    active_quiz = Quiz.query.filter_by(is_active=True).first()
    
    # Get quizzes this student has participated in (has at least one answer)
    completed_quizzes = db.session.query(Quiz)\
        .join(StudentAnswer, Quiz.quiz_id == StudentAnswer.quiz_id)\
        .filter(
            StudentAnswer.student_id == current_user.user_id,
            Quiz.is_active == False
        )\
        .distinct()\
        .order_by(Quiz.quiz_id.desc())\
        .all()
    
    return render_template('student/dashboard.html', 
                          active_quiz=active_quiz,
                          completed_quizzes=completed_quizzes)

@bp.route('/quiz/<int:quiz_id>/join')
@student_required
def join_quiz(quiz_id):
    """Join an active quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active:
        flash("This quiz is not currently active.")
        return redirect(url_for('student.dashboard'))
    
    return redirect(url_for('student.take_quiz', quiz_id=quiz_id))

@bp.route('/quiz/<int:quiz_id>/take')
@student_required
def take_quiz(quiz_id):
    """Take an active quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active:
        flash("This quiz is not currently active.")
        return redirect(url_for('student.dashboard'))
    
    # Get all questions for this quiz
    questions = quiz.questions
    
    # CRITICAL FIX: Get only questions answered in THIS specific quiz
    # This ensures we don't mark questions as answered if they were answered in other quizzes
    answered_question_ids = []
    
    # Get the quiz-specific answered question IDs
    result = db.session.query(StudentAnswer.question_id).filter(
        StudentAnswer.student_id == current_user.user_id,
        StudentAnswer.quiz_id == quiz_id
    ).all()
    
    answered_question_ids = [q[0] for q in result]
    
    return render_template('student/take_quiz.html', 
                          quiz=quiz, 
                          questions=questions,
                          answered_question_ids=answered_question_ids)

@bp.route('/quiz/<int:quiz_id>/question/<int:question_id>')
@student_required
def get_question(quiz_id, question_id):
    """Get a specific question for a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)
    
    # Check if the question belongs to the quiz
    if question not in quiz.questions:
        flash("This question is not part of the quiz.")
        return redirect(url_for('student.take_quiz', quiz_id=quiz_id))
    
    # Check if the student has already answered this question in this specific quiz
    existing_answer = StudentAnswer.query.filter_by(
        student_id=current_user.user_id,
        question_id=question_id,
        quiz_id=quiz_id
    ).first()
    
    return render_template('student/question.html', 
                          quiz=quiz, 
                          question=question,
                          existing_answer=existing_answer)

@bp.route('/quiz/<int:quiz_id>/question/<int:question_id>/submit', methods=['POST'])
@student_required
def submit_answer(quiz_id, question_id):
    """Submit an answer for a quiz question."""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)
    
    if not quiz.is_active:
        flash("This quiz is not currently active.")
        return redirect(url_for('student.dashboard'))
    
    # Check if the question belongs to the quiz
    if question not in quiz.questions:
        flash("This question is not part of the quiz.")
        return redirect(url_for('student.take_quiz', quiz_id=quiz_id))
    
    # Check if the student has already answered this question in this specific quiz
    existing_answer = StudentAnswer.query.filter_by(
        student_id=current_user.user_id,
        question_id=question_id,
        quiz_id=quiz_id
    ).first()
    
    if existing_answer:
        flash("You have already answered this question.")
        return redirect(url_for('student.take_quiz', quiz_id=quiz_id))
    
    # Get the selected choice
    choice_id = request.form.get('choice_id')
    if not choice_id:
        flash("Please select an answer.")
        return redirect(url_for('student.get_question', quiz_id=quiz_id, question_id=question_id))
    
    choice = Choice.query.get_or_404(choice_id)
    
    # Check if the choice belongs to the question
    if choice.question_id != question_id:
        flash("Invalid choice for this question.")
        return redirect(url_for('student.get_question', quiz_id=quiz_id, question_id=question_id))
    
    try:
        # Double check again for an existing answer to prevent race conditions
        existing_answer = StudentAnswer.query.filter_by(
            student_id=current_user.user_id,
            question_id=question_id,
            quiz_id=quiz_id
        ).first()
        
        if existing_answer:
            flash("You have already answered this question.")
            return redirect(url_for('student.take_quiz', quiz_id=quiz_id))
            
        # Record the student's answer
        answer = StudentAnswer(
            student_id=current_user.user_id,
            question_id=question_id,
            choice_id=choice_id,
            quiz_id=quiz_id
        )
        db.session.add(answer)
        db.session.commit()
        
        flash("Your answer has been recorded.")
        return redirect(url_for('student.take_quiz', quiz_id=quiz_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error recording your answer: {str(e)}")
        return redirect(url_for('student.get_question', quiz_id=quiz_id, question_id=question_id))

@bp.route('/quiz/<int:quiz_id>/results')
@student_required
def quiz_results(quiz_id):
    """View quiz results for the current student."""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get all questions for this quiz
    questions = quiz.questions
    
    # Get the student's answers for this quiz
    answers = db.session.query(
        Question.question_text,
        Choice.choice_text,
        StudentAnswer.is_correct
    ).join(
        StudentAnswer, Question.question_id == StudentAnswer.question_id
    ).join(
        Choice, StudentAnswer.choice_id == Choice.choice_id
    ).filter(
        StudentAnswer.quiz_id == quiz_id,
        StudentAnswer.student_id == current_user.user_id
    ).all()
    
    # Calculate the score
    total_questions = len(questions)
    answered_questions = len(answers)
    correct_answers = sum(1 for _, _, is_correct in answers if is_correct)
    
    return render_template('student/quiz_results.html', 
                          quiz=quiz, 
                          answers=answers,
                          total_questions=total_questions,
                          answered_questions=answered_questions,
                          correct_answers=correct_answers)

@bp.route('/api/quiz/current')
@student_required
def get_current_quiz_status():
    """API endpoint to get the current quiz status."""
    active_quiz = Quiz.query.filter_by(is_active=True).first()
    
    if not active_quiz:
        return jsonify({
            'active': False,
            'message': 'No active quiz'
        })
    
    return jsonify({
        'active': True,
        'quiz_id': active_quiz.quiz_id,
        'title': active_quiz.title
    })