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

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
});
