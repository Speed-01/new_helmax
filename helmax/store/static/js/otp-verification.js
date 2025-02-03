// Constants for OTP Timer and LocalStorage Key 
const OTP_TIMER_DURATION = 120; // Timer duration in seconds
const TIMER_START_KEY = 'otpTimerStart'; // Namespace for localStorage key

// Timer variables
let timerInterval;
const timerDisplay = document.getElementById('timer');
const resendBtn = document.getElementById('resend-btn');

// Function to calculate time left dynamically
function calculateTimeLeft() {
    const timerStart = localStorage.getItem(TIMER_START_KEY);
    if (timerStart) {
        const elapsedTime = Math.floor((Date.now() - parseInt(timerStart, 10)) / 1000);
        return Math.max(OTP_TIMER_DURATION - elapsedTime, 0);
    }
    return OTP_TIMER_DURATION;
}

// Initialize `timeLeft` using the `calculateTimeLeft` function
let timeLeft = calculateTimeLeft();

// Function to format and display the timer
function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Function to update the timer countdown
function updateTimer() {
    if (timeLeft <= 0) {
        clearInterval(timerInterval);
        timerDisplay.textContent = '00:00';
        resendBtn.disabled = false;
        localStorage.removeItem(TIMER_START_KEY);
        return;
    }

    updateTimerDisplay();
    timeLeft--;
}

// Function to start the timer
function startTimer() {
    if (timeLeft > 0) {
        if (!localStorage.getItem(TIMER_START_KEY)) {
            localStorage.setItem(TIMER_START_KEY, Date.now().toString());
        }
        updateTimerDisplay(); // Set the initial timer display
        timerInterval = setInterval(updateTimer, 1000);
        resendBtn.disabled = true;
    } else {
        timerDisplay.textContent = '00:00';
        resendBtn.disabled = false;
    }
}

// Start the timer on page load
startTimer();

function resendOTP() {
    resendBtn.disabled = true;

    fetch('/resend-otp/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            clearInterval(timerInterval);
            timeLeft = OTP_TIMER_DURATION;
            localStorage.setItem(TIMER_START_KEY, Date.now().toString());
            startTimer();
            displayMessage(data.message || 'OTP has been resent successfully.', 'success');
        } else {
            displayMessage(data.message || 'Failed to resend OTP. Please try again.', 'error');
            resendBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('An unexpected error occurred. Please try again.', 'error');
        resendBtn.disabled = false;
    });
}

function displayMessage(message, type) {
    const messageContainer = document.querySelector('.error-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `error-message ${type}`;
    msgDiv.textContent = message;
    messageContainer.innerHTML = '';
    messageContainer.appendChild(msgDiv);
}

// OTP Input Auto-Focus Logic
document.querySelectorAll('.otp-input').forEach((input, index) => {
    input.addEventListener('input', function () {
        if (this.value.length === 1 && index < 5) {
            document.querySelectorAll('.otp-input')[index + 1].focus();
        }
    });

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !this.value && index > 0) {
            document.querySelectorAll('.otp-input')[index - 1].focus();
        }
    });
});

// OTP Form Submission Logic
document.querySelector('.otp-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const otp = Array.from(document.querySelectorAll('.otp-input'))
        .map(input => input.value)
        .join('');

    if (otp.length !== 6 || !/^\d+$/.test(otp)) {
        displayMessage('Please enter a valid 6-digit OTP', 'error');
        return;
    }

    let hiddenInput = this.querySelector('input[name="otp"]');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'otp';
        this.appendChild(hiddenInput);
    }
    hiddenInput.value = otp;

    this.submit();
});
