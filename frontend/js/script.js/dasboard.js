// This block contains code for login/registration tabs and form submission.
// It's typically found on an 'index.html' or 'login.html' page.
// The outer 'if (loginTab && ...)' correctly ensures this code only runs if these elements exist.
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
        // In a real application, you'd collect username/password from the form
        // and send it to a backend API for authentication.
        // fetch('/api/login', { /* ... */ })
        // .then(...)
        // .catch(...)

        // Simulate API call and successful login
        setTimeout(() => {
            alert('Login successful! Redirecting to dashboard.');
            window.location.href = 'dashboard.html';
        }, 500);
    });

    registerForm.addEventListener('submit', (event) => {
        event.preventDefault();
        console.log('Registration attempt...');
        // In a real application, you'd collect registration details from the form
        // and send it to a backend API to create a new user.
        // fetch('/api/register', { /* ... */ })
        // .then(...)
        // .catch(...)

        // Simulate API call and successful registration
        setTimeout(() => {
            alert('Registration successful! Please log in.');
            window.location.href = 'index.html'; // Redirect back to login page
        }, 500);
    });
}

// --- Dashboard Specific Logic (or general navigation logic) ---
// This part is likely intended for pages like 'dashboard.html', 'quiz-listing.html', etc.

// Example: Highlight current page in navbar
const currentPath = window.location.pathname;
const navLinks = document.querySelectorAll('.navbar .nav-link');

navLinks.forEach(link => {
    // A more robust check for active links.
    // Compares the link's href to the current URL's path or filename.
    const linkHref = link.getAttribute('href');
    if (linkHref) {
        const linkFilename = linkHref.split('/').pop(); // E.g., 'dashboard.html'
        const currentFilename = currentPath.split('/').pop(); // E.g., 'dashboard.html'

        // Check for exact filename match or if the current path includes the link's href
        if (currentFilename === linkFilename || currentPath.includes(linkHref)) {
            link.classList.add('active-nav-link');
        }
    }
});

// Handle clicks on quiz rows to navigate to results (e.g., on dashboard or a quiz listing page)
const quizRows = document.querySelectorAll('.quiz-row a'); // Select the <a> tags within quiz rows
quizRows.forEach(rowLink => {
    rowLink.addEventListener('click', (event) => {
        // IMPORTANT NOTE: If the <a> tag already has a valid 'href' attribute
        // like 'quiz-results.html?quizId=XYZ', the browser will handle navigation by default.
        // This event listener is primarily for adding *additional* logic (like logging or analytics)
        // before the default navigation, or to fully control navigation with JavaScript.

        // If you want to PREVENT default navigation and handle it purely with JS:
        // event.preventDefault();

        const quizId = rowLink.closest('.quiz-row').dataset.quizId;
        // FIX: Use backticks for template literals in console.log
        console.log(`Navigating to results for Quiz ID: ${quizId}`);

        // If 'event.preventDefault()' was uncommented above, you would then
        // manually trigger navigation here, potentially after an async operation:
        // window.location.href = `quiz-results.html?quizId=${quizId}`;
    });
});

// You might also add logic here to dynamically load quizzes if you were using a real API
// (This would typically involve fetching data and populating elements on the page).