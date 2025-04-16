const originalFetch = window.fetch;

window.fetch = async function(url, options = {}) {
    // Only intercept relative URLs
    if (!url.startsWith('http') && !url.startsWith('//')) {
        const token = localStorage.getItem('firebaseToken');
        if (token) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }
        options.credentials = 'include';  // For cookie handling
    }
    return originalFetch(url, options);
};
 