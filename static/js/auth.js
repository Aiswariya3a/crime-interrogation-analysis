let authCheckInProgress = false;

auth.onAuthStateChanged(async (user) => {
    if (authCheckInProgress) return;
    authCheckInProgress = true;
    
    try {
        const currentPath = window.location.pathname;
        const isAuthPage = currentPath.includes('/auth');
        
        if (user) {
            // User is logged in
            if (!user.emailVerified) {
                await auth.signOut();
                if (!currentPath.includes('/auth/login')) {
                    window.location.href = '/auth/login';
                }
                return;
            }
            
            // If on auth pages, redirect to app
            if (isAuthPage && !currentPath.includes('mfa')) {
                window.location.href = '/index_realtime';
            }
        } else {
            // User is logged out
            if (!isAuthPage) {
                window.location.href = '/auth/login';
            }
        }
    } catch (error) {
        console.error('Auth state error:', error);
    } finally {
        authCheckInProgress = false;
    }
});


// Registration Function
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

// Password Reset
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
  if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
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
  if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
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
  document.getElementById('mfaForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const otp = e.target.otp.value;
    
    if (otp === '123456') {
        // Get and store the ID token
        const token = await auth.currentUser.getIdToken();
        localStorage.setItem('firebaseToken', token);
        
        // Redirect to protected route with token
        window.location.href = '/protected';
    } else {
        alert('Invalid OTP');
    }
});


  // Forgot Password Form
  if (document.getElementById('forgotForm')) {
    document.getElementById('forgotForm').addEventListener('submit', async (e) => {
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
});

 
// Refresh token every hour
setInterval(async () => {
    if (auth.currentUser) {
        const token = await auth.currentUser.getIdToken(true);
        localStorage.setItem('firebaseToken', token);
    }
}, 60 * 60 * 1000);

 
// Logout function
function logout() {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      return firebase.auth().signOut();
    })
    .then(() => {
      localStorage.removeItem('firebaseToken');
      window.location.href = '/auth/login';
    })
    .catch((error) => {
      console.error('Logout error:', error);
      alert('Error during logout: ' + error.message);
    });
}


// Add event listener for logout button
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }
});
 
