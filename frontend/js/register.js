import { registerUser } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('register-form').addEventListener('submit', handleRegistration);
});

async function handleRegistration(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        isVeteran: document.getElementById('veteran').checked,
        termsAccepted: document.getElementById('terms').checked
    };
    
    if (!formData.termsAccepted) {
        showMessage('message', 'Please accept the Terms & Conditions', true);
        return;
    }
    
    await registerUser(formData);
}
