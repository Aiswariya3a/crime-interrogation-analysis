// Shared auth functions
function showAlert(message, type = 'error') {
    const alertBox = document.getElementById('alert');
    if (!alertBox) return;
    
    alertBox.textContent = message;
    alertBox.className = `alert ${type}`;
    setTimeout(() => alertBox.style.display = 'none', 5000);
}

// Check auth state
auth.onAuthStateChanged(async (user) => {
    if (user) {
        // Verify email if on auth pages
        if (window.location.pathname.includes('/auth/')) {
            window.location.href = "{{ url_for('index') }}";
        }
        
        // Verify token with Flask backend
        const token = await user.getIdToken();
        const response = await fetch('/api/verify-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token })
        });
        
        if (!response.ok) {
            await auth.signOut();
            window.location.href = "{{ url_for('login') }}";
        }
    } else if (!window.location.pathname.includes('/auth/')) {
        window.location.href = "{{ url_for('login') }}";
    }
});