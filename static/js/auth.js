let isCheckingAuth = false; // Global flag to prevent loops

auth.onAuthStateChanged(user => {
    if (isCheckingAuth) return;
    isCheckingAuth = true;
    
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.includes('/auth');

    try {
        if (user) {
            // User is logged in
            if (!user.emailVerified) {
                auth.signOut();
                if (!currentPath.includes('/auth/login')) {
                    window.location.href = '/auth/login';
                }
                return;
            }

            // Only redirect if on auth pages (except MFA)
            if (isAuthPage && !currentPath.includes('/auth/mfa')) {
                window.location.href = '/index_realtime';
            }
        } else {
            // User is logged out - only redirect if not already on login page
            if (!isAuthPage) {
                window.location.href = '/auth/login';
            }
        }
    } finally {
        isCheckingAuth = false;
    }
});



// new joineeee !! 
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

// Password Reset should happen here.
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
document.getElementById('mfaForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const otp = e.target.otp.value;
    
    if (otp === '123456') {
        try {
            const user = auth.currentUser;
            if (!user) throw new Error("No authenticated user");
            
            const token = await user.getIdToken();
            
            // Store token in two places:
            localStorage.setItem('firebaseToken', token);
            
            // Set HTTP-only cookie via Flask endpoint
            const response = await fetch('/set_auth_cookie', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token
                }
            });
            
            if (!response.ok) throw new Error("Failed to set auth cookie");
            
            window.location.href = '/protected';
        } catch (error) {
            console.error('MFA verification failed:', error);
            alert('Authentication error: ' + error.message);
        }
    } else {
        alert('Invalid OTP code');
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
async function logout() {
  try {
    console.log("Pressed logout btn")
      // Show loading state
      const btn = document.getElementById('logoutBtn');
      if (btn) btn.disabled = true;

      // Sign out and CLEAR all auth-related data
      await auth.signOut();
      localStorage.removeItem('firebaseToken');
      sessionStorage.clear();

     
      window.location.replace('/auth/login'); // i used replace() instead of href to prevent history entry
  } catch (error) {
      console.error("Logout failed:", error);
      alert("Logout error. Please check console.");
  }
}


// firebase.auth().signOut().then(() => {
//   console.log("Successfully signed out from Firebase");
//   localStorage.removeItem('firebaseToken');  // Clear your token
//   window.location.href = "/auth/login";     // Redirect to login
// }).catch(error => {
//   console.error("Firebase signout error:", error);
// });

// Add event listener for logout button
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }
});
 
