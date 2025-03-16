# FilmClub Quizzer

A Flask-based web application for creating and participating in film-related quizzes. This application allows teachers to create quizzes with multiple-choice questions and run live quiz sessions. Students can join active quiz sessions and answer questions in real-time.

## Features

### Teacher Features
- User Management: Create, view, and delete student accounts
- Quiz Management: Create, edit, view and delete quizzes
- Question Management: Build and manage a question bank (also adding difficulty and categories for each question)
- Category Management: Add, edit, and delete categories for questions
- Quiz Creation: Choose categories to randomly select questions (and add manually additional questions if needed)
- Live Quiz Control: Start and end quiz sessions

### Student Features
- Quiz Participation: Join active quiz sessions
- Answer Submission: Answer questions
- Results: View own score at the end of the quiz

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd filmclub_quizzer
```

2. Create a virtual environment and activate it:
```
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up environment variables (or use the provided .env file):
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URI=sqlite:///instance/filmclub_quizzer_dev.db
```

## Database Setup

Initialize the database and create test data:
```
flask init-db
flask create-test-data
```

## Running the Application

Start the Flask development server:
```
python run.py
```

The application will be available at http://127.0.0.1:5000/

## Default Users

After running the `create-test-data` command, the following users will be available:

- Teacher: username `teacher`, password `password`
- Student 1: username `student1`, password `password`
- Student 2: username `student2`, password `password`

## Development

### Project Structure
- `app/`: Main application package
  - `__init__.py`: Application factory
  - `auth.py`: Authentication blueprint
  - `teacher.py`: Teacher blueprint (quiz creation, management)
  - `student.py`: Student blueprint (quiz participation)
  - `models.py`: Database models
  - `commands.py`: CLI commands for setup and testing
  - `templates/`: HTML templates
  - `static/`: Static files (CSS, JS)
- `instance/`: Instance-specific files (database)
- `run.py`: Application entry point

### Technologies Used
- Flask 2.3.3
- SQLAlchemy 2.0.23
- Flask-SQLAlchemy 3.1.1
- Flask-WTF 1.2.1
- Flask-Login 0.6.3
- SQLite Database
- Jinja2 Templating
- WTForms 3.1.0
- Python 3.x


## License

This project is licensed under the MIT License - see the LICENSE file for details. 