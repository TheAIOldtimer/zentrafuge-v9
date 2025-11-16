// frontend/js/onboarding.js - Complete onboarding flow

import Config from './config.js';
import { showMessage, showLoading } from './utils.js';

let currentStep = 0;
const totalSteps = 7;  // FIXED: Steps 0-6 = 7 total steps

document.addEventListener('DOMContentLoaded', () => {
    initializeOnboarding();
});

function initializeOnboarding() {
    console.log('🎯 Initializing onboarding...');
    
    // Check authentication (async - wait for Firebase to be ready)
    checkAuth();
    
    // Setup navigation buttons
    setupNavigationButtons();
    
    // Setup name suggestion buttons
    setupNameButtons();
    
    // Setup veteran checkbox toggle
    setupVeteranToggle();
    
    // Setup completion button
    setupCompletionButton();
    
    // Show first step
    showStep(0);
}

async function checkAuth() {
    // FIXED: Wait for Firebase auth state instead of checking currentUser immediately
    console.log('🔐 Checking authentication...');
    
    return new Promise((resolve, reject) => {
        const unsubscribe = firebase.auth().onAuthStateChanged((user) => {
            unsubscribe(); // Stop listening after first check
            
            if (!user) {
                console.log('❌ No user found, redirecting to login');
                window.location.href = '/';
                reject('No user');
            } else {
                console.log('✅ User authenticated:', user.uid);
                resolve(user);
            }
        });
    });
}

function setupNavigationButtons() {
    // Next buttons
    document.querySelectorAll('.onboarding-next').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep < totalSteps - 1) {
                currentStep++;
                showStep(currentStep);
                updateProgress();
            }
        });
    });
    
    // Previous buttons
    document.querySelectorAll('.onboarding-prev').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
                updateProgress();
            }
        });
    });
}

function setupNameButtons() {
    document.querySelectorAll('.name-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('ai_name').value = btn.textContent;
        });
    });
}

function setupVeteranToggle() {
    const veteranCheckbox = document.getElementById('veteran');
    const veteranDetails = document.getElementById('veteran-details');
    
    if (veteranCheckbox && veteranDetails) {
        veteranCheckbox.addEventListener('change', () => {
            veteranDetails.style.display = veteranCheckbox.checked ? 'block' : 'none';
        });
    }
}

function setupCompletionButton() {
    const completeBtn = document.getElementById('complete-onboarding');
    if (completeBtn) {
        completeBtn.addEventListener('click', completeOnboarding);
    }
    
    const enterChatBtn = document.getElementById('enter-chat');
    if (enterChatBtn) {
        enterChatBtn.addEventListener('click', () => {
            window.location.href = '/html/chat.html';
        });
    }
}

function showStep(step) {
    // Hide all steps
    for (let i = 0; i < totalSteps; i++) {
        const stepElement = document.getElementById(`onboarding-step-${i}`);
        if (stepElement) {
            stepElement.style.display = 'none';
        }
    }
    
    // Show current step
    const currentStepElement = document.getElementById(`onboarding-step-${step}`);
    if (currentStepElement) {
        currentStepElement.style.display = 'block';
    }
    
    console.log(`📍 Showing step ${step}`);
}

function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        const percentage = ((currentStep + 1) / totalSteps) * 100;
        progressFill.style.width = `${percentage}%`;
    }
}

function getSelectedRadioValue(name) {
    const selected = document.querySelector(`input[name="${name}"]:checked`);
    return selected ? selected.value : null;
}

function getSelectedCheckboxValues(name) {
    const selected = document.querySelectorAll(`input[name="${name}"]:checked`);
    return Array.from(selected).map(cb => cb.value);
}

async function completeOnboarding() {
    try {
        showLoading('onboarding-loading', true);
        showMessage('onboarding-message', '');
        
        console.log('🔄 Starting onboarding completion...');
        
        // Get current user
        const user = firebase.auth().currentUser;
        if (!user) {
            throw new Error('User not authenticated');
        }
        
        console.log('👤 User authenticated:', user.uid);
        
        // Collect all onboarding data
        const onboardingData = {
            cael_name: document.getElementById('ai_name')?.value || 'Cael',
            communication_style: getSelectedRadioValue('communication_style') || 'balanced',
            emotional_pacing: getSelectedRadioValue('emotional_pacing') || 'varies_situation',
            life_chapter: document.getElementById('life_chapter')?.value || '',
            sources_of_meaning: getSelectedCheckboxValues('sources_of_meaning'),
            effective_support: getSelectedCheckboxValues('effective_support'),
            veteran_profile: {
                is_veteran: document.getElementById('veteran')?.checked || false,
                service_branch: document.getElementById('service_branch')?.value || null,
                service_country: document.getElementById('service_country')?.value || 'US',
                service_years: document.getElementById('service_years')?.value || null,
                unit_served: document.getElementById('unit_served')?.value || null,
                deployments: document.getElementById('deployments')?.value || null,
                verification_status: 'pending'
            },
            personality_profile: {
                communication_preference: getSelectedRadioValue('communication_style'),
                emotional_processing: getSelectedRadioValue('emotional_pacing'),
                meaning_sources: getSelectedCheckboxValues('sources_of_meaning'),
                preferred_support: getSelectedCheckboxValues('effective_support')
            }
        };
        
        console.log('📤 Sending onboarding data:', onboardingData);
        
        // Get Firebase token
        const token = await user.getIdToken();
        console.log('🔑 Got Firebase token');
        
        // Send to backend
        const response = await fetch(`${Config.API_BASE}/user/onboarding`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(onboardingData)
        });
        
        console.log('📡 Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('❌ Backend error:', errorData);
            throw new Error(errorData.error || 'Failed to complete onboarding');
        }
        
        const result = await response.json();
        console.log('✅ Onboarding completed successfully:', result);
        
        // FIXED: Show completion step (step 6, not step 5)
        currentStep = 6;
        showStep(6);
        updateProgress();
        
        showMessage('onboarding-message', 'Setup completed successfully!', false);
        
    } catch (error) {
        console.error('❌ Onboarding error:', error);
        showMessage('onboarding-message', `Failed to complete setup: ${error.message}`, true);
    } finally {
        showLoading('onboarding-loading', false);
    }
}
