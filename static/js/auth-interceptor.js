 const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    // Add token to protected routes
    if (url.startsWith('/protected') || url.startsWith('/api')) {
        const token = localStorage.getItem('firebaseToken');
        if (!token) {
            window.location.href = '/auth/login';
            return;
        }
        
        options.headers = options.headers || {};
        options.headers['Authorization'] = token;
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