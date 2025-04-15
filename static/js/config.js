const firebaseConfig = {
    apiKey: "{{ config.FIREBASE_API_KEY }}",
    authDomain: "{{ config.FIREBASE_AUTH_DOMAIN }}",
    projectId: "{{ config.FIREBASE_PROJECT_ID }}",
    storageBucket: "{{ config.FIREBASE_STORAGE_BUCKET }}",
    messagingSenderId: "{{ config.FIREBASE_SENDER_ID }}",
    appId: "{{ config.FIREBASE_APP_ID }}"
  };
  
  const app = firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();
  