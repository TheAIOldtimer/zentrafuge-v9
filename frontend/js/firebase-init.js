// frontend/js/firebase-init.js
// Firebase v8 global initialization

(function () {
  if (window.firebase && firebase.apps && firebase.apps.length) {
    console.log("Firebase already initialized");
    return;
  }

  const firebaseConfig = {
    apiKey: "AIzaSyBGFZ20q4PagwvhvEuQIoIAb2_9w-Lt3b0",
    authDomain: "zentrafuge-v9-uk-veterans.firebaseapp.com",
    projectId: "zentrafuge-v9-uk-veterans",
    storageBucket: "zentrafuge-v9-uk-veterans.appspot.com", // ✅ correct suffix
    messagingSenderId: "231055123869",
    appId: "1:231055123869:web:2185ee6131bb3044ba7b74"
  };

  if (!window.firebase) {
    console.error("Firebase SDK not loaded before firebase-init.js");
    return;
  }

  firebase.initializeApp(firebaseConfig);
  console.log("✅ Firebase initialized (frontend v8 global SDK)");
})();
