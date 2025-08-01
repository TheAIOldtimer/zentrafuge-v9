// frontend/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyA0UGTSall_tMMIQWd7PBrjM-xIibiAQ-8",
  authDomain: "zentrafuge-v9.firebaseapp.com",
  projectId: "zentrafuge-v9",
  storageBucket: "zentrafuge-v9.appspot.com",
  messagingSenderId: "188961704770",
  appId: "1:188961704770:web:91de60d7aa0c696c52d6db",
  measurementId: "G-X5YXZMLNW4"
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
