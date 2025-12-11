// Dark mode toggle functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return; // Exit if toggle doesn't exist
    
    const body = document.body;
    const icon = darkModeToggle.querySelector('i');
    
    // Check for saved preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        body.classList.add('dark-mode');
        icon.classList.replace('bi-moon-fill', 'bi-sun-fill');
    }
    
    darkModeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        
        if (body.classList.contains('dark-mode')) {
            icon.classList.replace('bi-moon-fill', 'bi-sun-fill');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            icon.classList.replace('bi-sun-fill', 'bi-moon-fill');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
}

// Hamburger menu dropdown functionality
function initHamburgerMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    
    if (!hamburgerBtn || !dropdownMenu) return;
    
    // Toggle dropdown on button click
    hamburgerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!hamburgerBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.remove('show');
        }
    });
    
    // Close dropdown when clicking a link
    dropdownMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            dropdownMenu.classList.remove('show');
        });
    });
}

// Keyboard navigation for prev/next artist pages
function initKeyboardNavigation() {
    // Find prev/next links by data attributes
    const prevLink = document.querySelector('[data-nav-prev]');
    const nextLink = document.querySelector('[data-nav-next]');
    
    if (!prevLink && !nextLink) return; // Exit if no navigation links
    
    document.addEventListener('keydown', (e) => {
        // Ignore if user is typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Left arrow key - go to previous artist
        if (e.key === 'ArrowLeft' && prevLink) {
            const url = prevLink.getAttribute('data-nav-prev');
            if (url) {
                window.location.href = url;
            }
        }
        
        // Right arrow key - go to next artist
        if (e.key === 'ArrowRight' && nextLink) {
            const url = nextLink.getAttribute('data-nav-next');
            if (url) {
                window.location.href = url;
            }
        }
    });
}

// Touch swipe navigation for mobile
function initSwipeNavigation() {
    // Find prev/next links by data attributes
    const prevLink = document.querySelector('[data-nav-prev]');
    const nextLink = document.querySelector('[data-nav-next]');
    
    if (!prevLink && !nextLink) return; // Exit if no navigation links
    
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    const minSwipeDistance = 100; // Minimum horizontal distance for a swipe (increased from 50)
    const maxVerticalDistance = 80; // Maximum vertical movement allowed
    
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const horizontalDistance = touchEndX - touchStartX;
        const verticalDistance = Math.abs(touchEndY - touchStartY);
        
        // Ignore if too much vertical movement (likely scrolling)
        if (verticalDistance > maxVerticalDistance) {
            return;
        }
        
        // Swipe right (prev artist)
        if (horizontalDistance > minSwipeDistance && prevLink) {
            const url = prevLink.getAttribute('data-nav-prev');
            if (url) {
                window.location.href = url;
            }
        }
        
        // Swipe left (next artist)
        if (horizontalDistance < -minSwipeDistance && nextLink) {
            const url = nextLink.getAttribute('data-nav-next');
            if (url) {
                window.location.href = url;
            }
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initHamburgerMenu();
    initKeyboardNavigation();
    initSwipeNavigation();
});
