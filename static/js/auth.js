// Global flag to prevent loops
let isCheckingAuth = false;
let isInitialAuthCheck = true;

// Only run auth check if Firebase auth is available
if (typeof auth !== 'undefined') {
    auth.onAuthStateChanged(user => {
        if (isCheckingAuth) return;
        isCheckingAuth = true;
        
        try {
            const currentPath = window.location.pathname;
            const isAuthPage = currentPath.includes('/auth');

            if (user) {
                // User is logged in
                if (!user.emailVerified) {
                    auth.signOut();
                    if (!isAuthPage) {
                        window.location.href = '/auth/login';
                    }
                    return;
                }

                // Only redirect if on auth pages (except MFA) and this is not the initial page load
                if (isAuthPage && !currentPath.includes('/auth/mfa') && !isInitialAuthCheck) {
                    window.location.href = '/index_realtime';
                }
            } else {
                // User is logged out - only redirect if not already on login page and not initial check
                if (!isAuthPage && !isInitialAuthCheck) {
                    window.location.href = '/auth/login';
                }
            }
        } finally {
            isCheckingAuth = false;
            isInitialAuthCheck = false;
        }
    });
}

// Register Function
const handleRegister = async (email, password) => {
    try {
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        await userCredential.user.sendEmailVerification();
        return userCredential;
    } catch (error) {
        throw error;
    }
};

// Login Function
const handleLogin = async (email, password) => {
    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        if (!userCredential.user.emailVerified) {
            await auth.signOut();
            throw new Error('Please verify your email first');
        }
        return userCredential;
    } catch (error) {
        throw error;
    }
};

// Password Reset Function
const handlePasswordReset = async (email) => {
    try {
        await auth.sendPasswordResetEmail(email);
        return true;
    } catch (error) {
        throw error;
    }
};

// DOM Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Login Form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.email.value;
            const password = e.target.password.value;
            
            try {
                await handleLogin(email, password);
                window.location.href = '/auth/mfa';
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // Registration Form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.email.value;
            const password = e.target.password.value;
            
            try {
                await handleRegister(email, password);
                alert('Registration successful! Please check your email for verification.');
                window.location.href = '/auth/login';
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // MFA Form
    const mfaForm = document.getElementById('mfaForm');
    if (mfaForm) {
        mfaForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const otp = e.target.otp.value;

            if (otp === '123456') {
                try {
                    const user = auth.currentUser;
                    if (!user) throw new Error("No authenticated user");

                    // 1. Get fresh ID token
                    const token = await user.getIdToken();
                    
                    // 2. Store token in localStorage for API requests
                    localStorage.setItem('firebaseToken', token);
                    
                    // 3. Set HTTP-only cookie via Flask endpoint
                    const cookieResponse = await fetch('/set_auth_cookie', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': token
                        },
                        credentials: 'include'  // Required for cookies
                    });
                    
                    if (!cookieResponse.ok) {
                        throw new Error("Failed to set auth cookie");
                    }
                    
                    // 4. Redirect to protected route
                    window.location.href = '/index_realtime';
                } catch (error) {
                    console.error('MFA verification failed:', error);
                    alert('Authentication error: ' + error.message);
                }
            } else {
                alert('Invalid OTP code');
            }
        });
    }

    // Forgot Password Form
    const forgotForm = document.getElementById('forgotForm');
    if (forgotForm) {
        forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.email.value;
            
            try {
                await handlePasswordReset(email);
                alert('Password reset link sent to your email');
            } catch (error) {
                alert(error.message);
            }
        });
    }

  async function logout() {
      try {
        // 1. Sign out from Firebase
        await auth.signOut();
        
        // 2. Clear client-side storage
        localStorage.removeItem('firebaseToken');
        
        // 3. Redirect to the server logout endpoint that clears cookies
        // Using window.location directly since we want a GET request
        window.location.href = '/logout';
        
        // No need to redirect after this as the server will handle it
      } catch (error) {
        console.error('Logout error:', error);
        alert('Logout failed: ' + error.message);
      }
    }
    
});

// Refresh token every hour
setInterval(async () => {
    if (auth && auth.currentUser) {
        try {
            const token = await auth.currentUser.getIdToken(true);
            localStorage.setItem('firebaseToken', token);
        } catch (error) {
            console.error("Token refresh error:", error);
        }
    }
}, 60 * 60 * 1000);

// Fixed logout function to match the Flask route expectation (GET instead of POST)
async function logout() {
    try {
        // 1. Sign out from Firebase
        await auth.signOut();
        
        // 2. Clear client-side storage
        localStorage.removeItem('firebaseToken');
        
        // 3. Call server-side logout to clear cookie
        const response = await fetch('/logout', {
            method: 'GET',  // Changed from POST to GET to match Flask route
            credentials: 'include'  // Required for cookie handling
        });
        
        // 4. Redirect to login page regardless of response
        window.location.href = '/auth/login';
    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect even if there's an error
        window.location.href = '/auth/login';
    }
}