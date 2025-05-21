const firebaseConfig = {
  apiKey: "AIzaSyAGoeL9aPqqBtHSgYsahFLhde_ayBlAyi0",
  authDomain: "rtcia-7734f.firebaseapp.com",
  projectId: "rtcia-7734f",
  storageBucket: "rtcia-7734f.firebasestorage.app",
  messagingSenderId: "126641824647",
  appId: "1:126641824647:web:3bc05ccaf019b75d7c6922",
  measurementId: "G-P46P93HVFJ"
};

const app = firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
window.firebaseAuth = firebase.auth(app);
