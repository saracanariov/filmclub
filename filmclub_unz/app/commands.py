import click
from flask.cli import with_appcontext
from . import db
from .models import User, Category, Question, Choice, Quiz, StudentAnswer

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')

@click.command('migrate-student-answers')
@with_appcontext
def migrate_student_answers_command():
    """Migrate student answers to include quiz_id."""
    from sqlalchemy import text
    
    # First check if quiz_id column exists
    conn = db.engine.connect()
    result = conn.execute(text("PRAGMA table_info(student_answers)"))
    
    # Fix: SQLite returns rows as tuples, not dictionaries
    # Column indices: 0=cid, 1=name, 2=type, 3=notnull, 4=dflt_value, 5=pk
    columns = [row[1] for row in result]
    
    if 'quiz_id' not in columns:
        # Add the quiz_id column
        conn.execute(text("ALTER TABLE student_answers ADD COLUMN quiz_id INTEGER REFERENCES quizzes(quiz_id) ON DELETE CASCADE"))
        click.echo("Added quiz_id column to student_answers table")
        
        # Now we need to populate the quiz_id for existing answers
        # For each answer, find a quiz that contains the question and use its ID
        answers = StudentAnswer.query.all()
        
        # Get all quiz questions to avoid repetitive queries
        from .models import QuizQuestion
        
        # Find quiz IDs for each question
        quiz_mapping = {}
        quiz_questions = QuizQuestion.query.all()
        for qq in quiz_questions:
            if qq.question_id not in quiz_mapping:
                quiz_mapping[qq.question_id] = qq.quiz_id
        
        # Update each answer with the appropriate quiz ID
        updated_count = 0
        for answer in answers:
            if answer.question_id in quiz_mapping:
                answer.quiz_id = quiz_mapping[answer.question_id]
                updated_count += 1
        
        db.session.commit()
        click.echo(f"Updated {updated_count} student answers with quiz IDs")
    else:
        click.echo("quiz_id column already exists in student_answers table")

@click.command('create-test-data')
@with_appcontext
def create_test_data_command():
    """Create some test data for development."""
    # Create users
    teacher = User(username='teacher', password='password', role='teacher')
    student1 = User(username='student1', password='password', role='student')
    student2 = User(username='student2', password='password', role='student')
    
    db.session.add_all([teacher, student1, student2])
    db.session.commit()
    
    # Create categories
    categories = [
        Category(category_name='Oscars'),
        Category(category_name='Genres'),
        Category(category_name='Directors'),
        Category(category_name='Actors'),
        Category(category_name='2000s')
    ]
    
    db.session.add_all(categories)
    db.session.commit()
    
    # Create questions with choices
    questions = [
        {
            'text': 'Which film won the Best Picture Oscar in 2020?',
            'difficulty': 'Medium',
            'categories': [categories[0], categories[4]],  # Oscars, 2000s
            'choices': [
                {'text': 'Parasite', 'correct': True},
                {'text': '1917', 'correct': False},
                {'text': 'Joker', 'correct': False},
                {'text': 'Once Upon a Time in Hollywood', 'correct': False}
            ]
        },
        {
            'text': 'Who directed "Pulp Fiction"?',
            'difficulty': 'Easy',
            'categories': [categories[2]],  # Directors
            'choices': [
                {'text': 'Quentin Tarantino', 'correct': True},
                {'text': 'Martin Scorsese', 'correct': False},
                {'text': 'Steven Spielberg', 'correct': False},
                {'text': 'Christopher Nolan', 'correct': False}
            ]
        },
        {
            'text': 'Which actor played Tony Stark/Iron Man in the Marvel Cinematic Universe?',
            'difficulty': 'Easy',
            'categories': [categories[3], categories[4]],  # Actors, 2000s
            'choices': [
                {'text': 'Robert Downey Jr.', 'correct': True},
                {'text': 'Chris Evans', 'correct': False},
                {'text': 'Chris Hemsworth', 'correct': False},
                {'text': 'Mark Ruffalo', 'correct': False}
            ]
        },
        {
            'text': 'Which of these films is NOT a musical?',
            'difficulty': 'Medium',
            'categories': [categories[1]],  # Genres
            'choices': [
                {'text': 'The Shawshank Redemption', 'correct': True},
                {'text': 'La La Land', 'correct': False},
                {'text': 'The Greatest Showman', 'correct': False},
                {'text': 'Mamma Mia!', 'correct': False}
            ]
        },
        {
            'text': 'Who won the Best Actress Oscar for her role in "La La Land"?',
            'difficulty': 'Hard',
            'categories': [categories[0], categories[3], categories[4]],  # Oscars, Actors, 2000s
            'choices': [
                {'text': 'Emma Stone', 'correct': True},
                {'text': 'Emma Watson', 'correct': False},
                {'text': 'Jennifer Lawrence', 'correct': False},
                {'text': 'Natalie Portman', 'correct': False}
            ]
        }
    ]
    
    for q_data in questions:
        question = Question(question_text=q_data['text'], difficulty=q_data['difficulty'])
        db.session.add(question)
        db.session.flush()  # Flush to get the question_id
        
        # Add categories
        for category in q_data['categories']:
            question.categories.append(category)
        
        # Add choices
        for c_data in q_data['choices']:
            choice = Choice(
                question_id=question.question_id,
                choice_text=c_data['text'],
                is_correct=c_data['correct']
            )
            db.session.add(choice)
    
    db.session.commit()
    
    # Create a sample quiz
    quiz = Quiz(
        title='Film Trivia Mix',
        question_count=5,
        difficulty='Medium',
        created_by=teacher.user_id
    )
    db.session.add(quiz)
    db.session.flush()
    
    # Add all questions to the quiz
    for question in Question.query.all():
        quiz.questions.append(question)
    
    db.session.commit()
    
    click.echo('Created test data.')

@click.command('fix-student-answers-constraint')
@with_appcontext
def fix_student_answers_constraint_command():
    """Fix the unique constraint on student_answers table."""
    from sqlalchemy import text
    import sqlite3
    
    conn = db.engine.connect()
    
    # Check SQLite version to determine approach
    result = conn.execute(text("SELECT sqlite_version()"))
    sqlite_version = result.scalar()
    click.echo(f"SQLite version: {sqlite_version}")
    
    # Get table info including constraints
    result = conn.execute(text("""
        SELECT sql FROM sqlite_master WHERE type='table' AND name='student_answers'
    """))
    table_sql = result.scalar()
    click.echo(f"Current table definition:")
    click.echo(table_sql)
    
    # For SQLite, we'll need to create a new table with the correct constraint
    try:
        # Create a temporary table with the correct schema
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS student_answers_new (
                sa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                choice_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                is_correct BOOLEAN DEFAULT 0,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_student_question UNIQUE (student_id, question_id),
                FOREIGN KEY (student_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (question_id) ON DELETE CASCADE,
                FOREIGN KEY (choice_id) REFERENCES choices (choice_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id) ON DELETE CASCADE
            )
        """))
        
        # Copy data from the old table to the new one
        # We need to handle the case where a student has multiple answers to the same question
        # across different quizzes (which the old constraint didn't allow)
        # First, we'll get all the data
        result = conn.execute(text("SELECT * FROM student_answers"))
        rows = result.fetchall()
        
        # Drop the new table if it exists to start fresh
        conn.execute(text("DROP TABLE IF EXISTS student_answers_new"))
        
        # Recreate it
        conn.execute(text("""
            CREATE TABLE student_answers_new (
                sa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                choice_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                is_correct BOOLEAN DEFAULT 0,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_student_question UNIQUE (student_id, question_id),
                FOREIGN KEY (student_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (question_id) ON DELETE CASCADE,
                FOREIGN KEY (choice_id) REFERENCES choices (choice_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id) ON DELETE CASCADE
            )
        """))
        
        # Copy data, ensuring quiz_id is set
        for row in rows:
            sa_id = row[0]
            student_id = row[1]
            question_id = row[2]
            choice_id = row[3]
            is_correct = row[4] if len(row) > 4 else 0
            submitted_at = row[5] if len(row) > 5 else "CURRENT_TIMESTAMP"
            quiz_id = row[6] if len(row) > 6 and row[6] is not None else 1  # Default to quiz 1 if not set
            
            conn.execute(text(f"""
                INSERT OR IGNORE INTO student_answers_new 
                (sa_id, student_id, question_id, choice_id, quiz_id, is_correct, submitted_at)
                VALUES ({sa_id}, {student_id}, {question_id}, {choice_id}, {quiz_id}, {is_correct}, '{submitted_at}')
            """))
        
        # Drop the old table
        conn.execute(text("DROP TABLE student_answers"))
        
        # Rename the new table to the original name
        conn.execute(text("ALTER TABLE student_answers_new RENAME TO student_answers"))
        
        click.echo("Fixed the unique constraint on student_answers table.")
        
        # Verify the new constraint
        result = conn.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='student_answers'
        """))
        new_table_sql = result.scalar()
        click.echo(f"New table definition:")
        click.echo(new_table_sql)
        
    except Exception as e:
        click.echo(f"Error fixing constraint: {str(e)}")
        raise

def init_app(app):
    """Register database commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_test_data_command)
    app.cli.add_command(migrate_student_answers_command)
    app.cli.add_command(fix_student_answers_constraint_command) 