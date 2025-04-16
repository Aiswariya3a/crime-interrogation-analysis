// Auth State Management
let currentUser = null;

// Initialize auth state listener
auth.onAuthStateChanged(user => {
  if (user && user.emailVerified) {
      // Check if we're already on the dashboard
      if (!window.location.pathname.includes('index_realtime')) {
          // Test if the route exists first
          fetch('/index_realtime')
              .then(response => {
                  if (response.ok) {
                      window.location.href = '/index_realtime';
                  } else {
                      console.error('Dashboard route not found');
                      // Fallback to a different page
                      window.location.href = '/protected';
                  }
              })
              .catch(error => {
                  console.error('Route check failed:', error);
              });
      }
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
  initAuth();
  
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

function logout() {
  auth.signOut();
  localStorage.removeItem('firebaseToken');
  window.location.href = '/auth/login';
}
