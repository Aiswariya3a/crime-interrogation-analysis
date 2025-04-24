const firebaseConfig = {
  apiKey: "AIzaSyDCjM67ZXmZlv6GtW98djPBdT64Y9eTWmM",
  authDomain: "rtia-75770.firebaseapp.com",
  projectId: "rtia-75770",
  storageBucket: "rtia-75770.firebasestorage.app",
  messagingSenderId: "1079741983361",
  appId: "1:1079741983361:web:db6f367e8b6fe9cf6efb80",
};

const app = firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
window.firebaseAuth = firebase.auth(app);
