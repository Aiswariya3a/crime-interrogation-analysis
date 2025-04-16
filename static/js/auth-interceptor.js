// Add this to your static JS files
const originalFetch = window.fetch;

window.fetch = async function(url, options = {}) {
    // Add token to all API requests
    if (!url.startsWith('http')) { // Only intercept relative URLs
        const token = localStorage.getItem('firebaseToken');
        if (token) {
            options.headers = {
                ...options.headers,
                'Authorization': token
            };
        }
    }
    return originalFetch(url, options);
};


// Also handle page navigation
window.addEventListener('popstate', () => {
    const token = localStorage.getItem('firebaseToken');
    if (!token && window.location.pathname.includes('/protected')) {
        window.location.href = '/auth/login';
    }
});
