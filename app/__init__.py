import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Set default configuration
    #app.config.from_mapping(
    #    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    #    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///instance/filmclub_quizzer_dev.db'),
    #    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    #)

    # Set default configuration - on Render
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance', 'filmclub_quizzer_dev.db')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .teacher import bp as teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/teacher')

    from .student import bp as student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    # Register CLI commands
    from . import models
    from . import commands
    commands.init_app(app)

    # Context processor for templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Homepage route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app 