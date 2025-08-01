// js/login.js - Login page logic

import { loginUser } from './auth.js';
import { showMessage } from './utils.js';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Check if user is already logged in
    checkAuthState();
});

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    // Basic validation
    if (!email) {
        showMessage('message', 'Please enter your email address', true);
        return;
    }
    
    if (!password) {
        showMessage('message', 'Please enter your password', true);
        return;
    }
    
    // Attempt login
    await loginUser(email, password);
}

function checkAuthState() {
    // Check if Firebase is ready and user is already logged in
    if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
        firebase.auth().onAuthStateChanged((user) => {
            if (user) {
                // User is already logged in, redirect to chat
                window.location.href = 'html/chat.html';
            }
        });
    }
}
