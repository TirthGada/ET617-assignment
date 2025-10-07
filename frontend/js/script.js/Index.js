document.addEventListener('DOMContentLoaded', () => {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginTab && registerTab && loginForm && registerForm) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
            // In a real app, you might redirect or clear forms here
        });

        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
            // In a real app, you might redirect or clear forms here
        });

        // Example: Handle form submissions (front-end only)
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault();
            alert('Login attempt (frontend only)');
            // In a real app, send data to backend and on success, redirect to dashboard.html
            window.location.href = 'dashboard.html'; // Simulate redirect
        });

        registerForm.addEventListener('submit', (event) => {
            event.preventDefault();
            alert('Registration attempt (frontend only)');
            // In a real app, send data to backend and on success, redirect to login page or dashboard.
            window.location.href = 'index.html'; // After registration, go back to login
        });
    }
});