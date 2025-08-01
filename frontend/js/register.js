// js/register.js - Registration page logic

import { registerUser } from './auth.js';
import { showMessage } from './utils.js';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('register-form').addEventListener('submit', handleRegistration);
});

async function handleRegistration(e) {
    e.preventDefault();
    
    // Collect form data
    const formData = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        isVeteran: document.getElementById('veteran').checked,
        termsAccepted: document.getElementById('terms').checked
    };
    
    // Validation
    if (!formData.name) {
        showMessage('message', 'Please enter your full name', true);
        return;
    }
    
    if (!formData.email) {
        showMessage('message', 'Please enter your email address', true);
        return;
    }
    
    if (!formData.password || formData.password.length < 6) {
        showMessage('message', 'Password must be at least 6 characters', true);
        return;
    }
    
    if (!formData.termsAccepted) {
        showMessage('message', 'Please accept the Terms & Conditions', true);
        return;
    }
    
    // Attempt registration
    await registerUser(formData);
}
