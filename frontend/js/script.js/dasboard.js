if (loginTab && registerTab && loginForm && registerForm) {
    loginTab.addEventListener('click', () => {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
    });

    registerTab.addEventListener('click', () => {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
    });

    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        console.log('Login attempt...');
        // Simulate API call and successful login
        setTimeout(() => {
            alert('Login successful! Redirecting to dashboard.');
            window.location.href = 'dashboard.html';
        }, 500);
    });

    registerForm.addEventListener('submit', (event) => {
        event.preventDefault();
        console.log('Registration attempt...');
        // Simulate API call and successful registration
        setTimeout(() => {
            alert('Registration successful! Please log in.');
            window.location.href = 'index.html'; // Redirect back to login
        }, 500);
    });
}

// --- Dashboard Specific Logic (if needed) ---
// Example: Highlight current page in navbar (basic, for demonstration)
const currentPath = window.location.pathname;
const navLinks = document.querySelectorAll('.navbar .nav-link');

navLinks.forEach(link => {
    if (link.href && currentPath.includes(link.getAttribute('href'))) {
        link.classList.add('active-nav-link');
    }
});

// Handle clicks on quiz rows to navigate to results
const quizRows = document.querySelectorAll('.quiz-row a'); // Select the <a> tags within quiz rows
quizRows.forEach(rowLink => {
    rowLink.addEventListener('click', (event) => {
        // The href already handles navigation, but you could add more logic here
        // event.preventDefault(); // Uncomment if you want to prevent default navigation and handle it purely with JS
        const quizId = rowLink.closest('.quiz-row').dataset.quizId;
        console.log(Navigating to results for Quiz ID: ${quizId});
        // window.location.href = quiz-results.html?quizId=${quizId}; // Already handled by href
    });
});

// You might also add logic here to dynamically load quizzes if you were using a real API