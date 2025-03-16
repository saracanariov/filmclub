// Main JavaScript file for FilmClub Quizzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any components that need JavaScript
    initFlashMessages();
    initQuizPolling();
});

// Auto-hide flash messages after 5 seconds
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
}

// Poll for quiz status updates (for students)
function initQuizPolling() {
    // Only run on student dashboard
    const studentDashboard = document.getElementById('student-dashboard');
    if (!studentDashboard) return;
    
    const quizStatusElement = document.getElementById('quiz-status');
    if (!quizStatusElement) return;
    
    // Poll every 5 seconds
    setInterval(function() {
        fetch('/student/api/quiz/current')
            .then(response => response.json())
            .then(data => {
                if (data.active) {
                    quizStatusElement.innerHTML = `
                        <div class="card">
                            <h3 class="card-title">Active Quiz</h3>
                            <p>Quiz: ${data.title}</p>
                            <a href="/student/quiz/${data.quiz_id}/join" class="btn btn-success">Join Quiz</a>
                        </div>
                    `;
                } else {
                    quizStatusElement.innerHTML = `
                        <div class="card">
                            <h3 class="card-title">No Active Quiz</h3>
                            <p>There is no active quiz at the moment. Please wait for your teacher to start one.</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error polling for quiz status:', error);
            });
    }, 5000);
}

// Dynamic form fields for question creation
function addChoiceField() {
    const choicesContainer = document.getElementById('choices-container');
    if (!choicesContainer) return;
    
    const choiceCount = choicesContainer.querySelectorAll('.choice-row').length;
    
    const newRow = document.createElement('div');
    newRow.className = 'choice-row form-group';
    newRow.innerHTML = `
        <div style="display: flex; align-items: center;">
            <input type="text" name="choice_text" placeholder="Choice ${choiceCount + 1}" required>
            <label style="margin-left: 10px;">
                <input type="radio" name="is_correct" value="${choiceCount}"> Correct
            </label>
        </div>
    `;
    
    choicesContainer.appendChild(newRow);
}

// Quiz session control for teachers
function nextQuestion(quizId, currentQuestionIndex) {
    // Parse the current index as an integer and add 1
    const nextQuestionIndex = parseInt(currentQuestionIndex) + 1;
    window.location.href = `/teacher/quizzes/${quizId}/session?question=${nextQuestionIndex}`;
}

function previousQuestion(quizId, currentQuestionIndex) {
    // Parse the current index as an integer
    const currentIndex = parseInt(currentQuestionIndex);
    if (currentIndex > 0) {
        const prevQuestionIndex = currentIndex - 1;
        window.location.href = `/teacher/quizzes/${quizId}/session?question=${prevQuestionIndex}`;
    }
}

// Confirm delete actions
function confirmDelete(message, formId) {
    if (confirm(message)) {
        document.getElementById(formId).submit();
    }
} 