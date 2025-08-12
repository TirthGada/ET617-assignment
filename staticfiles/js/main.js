// Main JavaScript for Learning Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Track general page interactions
    trackPageInteractions();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        });
    }, 5000);

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// Track page interactions for analytics
function trackPageInteractions() {
    // Track button clicks
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const buttonText = this.textContent.trim();
            const buttonClass = this.className;
            
            console.log('Button clicked:', buttonText);
            
            // You can expand this to send to analytics endpoint
            trackEvent('button_click', 'UI Component', `Button clicked: ${buttonText}`);
        });
    });

    // Track card clicks
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't track if clicking on buttons or links inside cards
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON' && 
                !e.target.closest('a') && !e.target.closest('button')) {
                
                const cardTitle = this.querySelector('.card-title');
                const title = cardTitle ? cardTitle.textContent.trim() : 'Unknown';
                
                console.log('Card clicked:', title);
                trackEvent('card_click', 'UI Component', `Card clicked: ${title}`);
            }
        });
    });

    // Track navigation clicks
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            const linkText = this.textContent.trim();
            console.log('Navigation clicked:', linkText);
            trackEvent('navigation_click', 'Navigation', `Navigation clicked: ${linkText}`);
        });
    });
}

// Generic event tracking function
function trackEvent(eventName, component, description) {
    // This is a placeholder for tracking events
    // In a real implementation, you would send this to your analytics endpoint
    const eventData = {
        event_name: eventName,
        component: component,
        description: description,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        user_agent: navigator.userAgent
    };
    
    console.log('Event tracked:', eventData);
    
    // You could send this to your Django backend:
    // fetch('/track-event/', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': getCookie('csrftoken')
    //     },
    //     body: JSON.stringify(eventData)
    // });
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Progress animation
function animateProgress(element, targetWidth, duration = 1000) {
    const startWidth = 0;
    const startTime = performance.now();
    
    function updateProgress(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentWidth = startWidth + (targetWidth - startWidth) * progress;
        
        element.style.width = currentWidth + '%';
        element.textContent = Math.round(currentWidth) + '%';
        
        if (progress < 1) {
            requestAnimationFrame(updateProgress);
        }
    }
    
    requestAnimationFrame(updateProgress);
}

// Animate progress bars on page load
window.addEventListener('load', function() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = parseFloat(bar.style.width) || parseFloat(bar.getAttribute('aria-valuenow')) || 0;
        if (targetWidth > 0) {
            bar.style.width = '0%';
            setTimeout(() => {
                animateProgress(bar, targetWidth);
            }, 500);
        }
    });
});

// Video player enhancements
function enhanceVideoPlayer(videoElement) {
    if (!videoElement) return;
    
    // Track video events
    videoElement.addEventListener('loadstart', () => {
        console.log('Video loading started');
    });
    
    videoElement.addEventListener('canplay', () => {
        console.log('Video can start playing');
    });
    
    videoElement.addEventListener('ended', () => {
        console.log('Video ended');
        trackEvent('video_ended', 'Video Player', 'User watched video to completion');
    });
    
    // Add custom controls or overlays if needed
    const videoContainer = videoElement.parentElement;
    if (videoContainer) {
        // You can add custom video controls here
    }
}

// Initialize video players on pages that have them
document.addEventListener('DOMContentLoaded', function() {
    const videos = document.querySelectorAll('video');
    videos.forEach(enhanceVideoPlayer);
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
    
    // Ctrl/Cmd + Enter to submit forms
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            const submitBtn = activeForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.click();
            }
        }
    }
});

// Utility functions
const Utils = {
    // Format time duration
    formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
};

// Make Utils globally available
window.Utils = Utils; 