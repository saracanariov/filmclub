import os
import subprocess
import sys

def setup_database():
    """Initialize the database and create test data."""
    print("Setting up the FilmClub Quizzer database...")
    
    # Initialize the database
    print("Initializing the database...")
    subprocess.run([sys.executable, "-m", "flask", "init-db"])
    
    # Create test data
    print("Creating test data...")
    subprocess.run([sys.executable, "-m", "flask", "create-test-data"])
    
    print("Setup complete!")
    print("\nDefault users:")
    print("- Teacher: username 'teacher', password 'password'")
    print("- Student 1: username 'student1', password 'password'")
    print("- Student 2: username 'student2', password 'password'")
    
    print("\nTo run the application:")
    print("flask run")
    print("or")
    print("python run.py")

if __name__ == "__main__":
    # Set Flask environment variables
    os.environ["FLASK_APP"] = "app"
    
    # Run setup
    setup_database() 