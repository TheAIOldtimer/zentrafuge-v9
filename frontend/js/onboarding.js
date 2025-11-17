// frontend/js/onboarding.js - Complete onboarding flow (DEBUG VERSION)

import Config from './config.js';
import { showMessage, showLoading } from './utils.js';

let currentStep = 0;
const totalSteps = 7;  // Steps 0-6 = 7 total steps

console.log('🟢 onboarding.js loaded successfully');

document.addEventListener('DOMContentLoaded', () => {
    console.log('🟢 DOMContentLoaded fired');
    initializeOnboarding();
});

function initializeOnboarding() {
    console.log('🎯 Initializing onboarding...');
    
    // Check authentication
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
    
    console.log('✅ Onboarding initialization complete');
}

async function checkAuth() {
    console.log('🔐 Checking authentication...');
    
    return new Promise((resolve, reject) => {
        const unsubscribe = firebase.auth().onAuthStateChanged((user) => {
            unsubscribe();
            
            if (!user) {
                console.log('❌ No user found, redirecting to login');
                window.location.href = '/';
                reject('No user');
            } else {
                console.log('✅ User authenticated:', user.uid);
                console.log('📧 Email:', user.email);
                console.log('✉️ Email verified:', user.emailVerified);
                resolve(user);
            }
        });
    });
}

function setupNavigationButtons() {
    console.log('🔘 Setting up navigation buttons...');
    
    const nextButtons = document.querySelectorAll('.onboarding-next');
    const prevButtons = document.querySelectorAll('.onboarding-prev');
    
    console.log('   Found', nextButtons.length, 'next buttons');
    console.log('   Found', prevButtons.length, 'prev buttons');
    
    // Next buttons
    nextButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            console.log('➡️ Next button clicked, current step:', currentStep);
            if (currentStep < totalSteps - 1) {
                currentStep++;
                showStep(currentStep);
                updateProgress();
            }
        });
    });
    
    // Previous buttons
    prevButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            console.log('⬅️ Previous button clicked, current step:', currentStep);
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
                updateProgress();
            }
        });
    });
}

function setupNameButtons() {
    const nameButtons = document.querySelectorAll('.name-btn');
    console.log('📝 Setting up name buttons, found:', nameButtons.length);
    
    nameButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const name = btn.textContent;
            console.log('📝 Name button clicked:', name);
            document.getElementById('ai_name').value = name;
        });
    });
}

function setupVeteranToggle() {
    const veteranCheckbox = document.getElementById('veteran');
    const veteranDetails = document.getElementById('veteran-details');
    
    console.log('🎖️ Setting up veteran toggle');
    console.log('   Checkbox found:', !!veteranCheckbox);
    console.log('   Details section found:', !!veteranDetails);
    
    if (veteranCheckbox && veteranDetails) {
        veteranCheckbox.addEventListener('change', () => {
            const isChecked = veteranCheckbox.checked;
            console.log('🎖️ Veteran checkbox changed:', isChecked);
            veteranDetails.style.display = isChecked ? 'block' : 'none';
        });
    }
}

function setupCompletionButton() {
    const completeBtn = document.getElementById('complete-onboarding');
    const enterChatBtn = document.getElementById('enter-chat');
    
    console.log('✅ Setting up completion buttons');
    console.log('   Complete button found:', !!completeBtn);
    console.log('   Enter chat button found:', !!enterChatBtn);
    
    if (completeBtn) {
        console.log('✅ Attaching click handler to complete button');
        completeBtn.addEventListener('click', () => {
            console.log('🔵 COMPLETE BUTTON CLICKED!');
            completeOnboarding();
        });
    } else {
        console.error('❌ Complete button NOT FOUND! ID: complete-onboarding');
    }
    
    if (enterChatBtn) {
        enterChatBtn.addEventListener('click', () => {
            console.log('💬 Enter chat button clicked');
            window.location.href = '/html/chat.html';
        });
    }
}

function showStep(step) {
    console.log(`📍 Showing step ${step}`);
    
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
        console.log(`   ✅ Step ${step} now visible`);
    } else {
        console.error(`   ❌ Step ${step} element NOT FOUND!`);
    }
}

function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        const percentage = ((currentStep + 1) / totalSteps) * 100;
        progressFill.style.width = `${percentage}%`;
        console.log(`📊 Progress updated: ${percentage.toFixed(1)}%`);
    }
}

function getSelectedRadioValue(name) {
    const selected = document.querySelector(`input[name="${name}"]:checked`);
    const value = selected ? selected.value : null;
    console.log(`   Radio "${name}":`, value);
    return value;
}

function getSelectedCheckboxValues(name) {
    const selected = document.querySelectorAll(`input[name="${name}"]:checked`);
    const values = Array.from(selected).map(cb => cb.value);
    console.log(`   Checkboxes "${name}":`, values);
    return values;
}

async function completeOnboarding() {
    console.log('🔵🔵🔵 completeOnboarding FUNCTION CALLED! 🔵🔵🔵');
    
    try {
        console.log('1️⃣ Showing loading indicator...');
        showLoading('onboarding-loading', true);
        showMessage('onboarding-message', '');
        
        console.log('2️⃣ Waiting for Firebase auth state...');
        // CRITICAL: Wait for Firebase to be ready
        await new Promise((resolve) => {
            const unsubscribe = firebase.auth().onAuthStateChanged((user) => {
                unsubscribe();
                console.log('   Firebase auth state ready, user:', user?.uid);
                resolve();
            });
        });
        
        console.log('3️⃣ Getting current user...');
        const user = firebase.auth().currentUser;
        
        if (!user) {
            console.error('❌ CRITICAL: No user found after auth state check!');
            throw new Error('User not authenticated');
        }
        
        console.log('✅ User authenticated:', user.uid);
        console.log('   Email:', user.email);
        console.log('   Email verified:', user.emailVerified);
        
        console.log('4️⃣ Collecting onboarding data...');
        
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
        
        console.log('📤 Onboarding data collected:', JSON.stringify(onboardingData, null, 2));
        
        console.log('5️⃣ Getting Firebase ID token...');
        const token = await user.getIdToken();
        console.log('🔑 Token obtained (length:', token.length, ')');
        
        console.log('6️⃣ Sending to backend...');
        console.log('   API endpoint:', `${Config.API_BASE}/user/onboarding`);
        
        const response = await fetch(`${Config.API_BASE}/user/onboarding`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(onboardingData)
        });
        
        console.log('📡 Response received!');
        console.log('   Status:', response.status);
        console.log('   Status text:', response.statusText);
        console.log('   OK:', response.ok);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('❌ Backend returned error:', errorData);
            throw new Error(errorData.error || 'Failed to complete onboarding');
        }
        
        const result = await response.json();
        console.log('✅ Backend response:', result);
        
        console.log('7️⃣ Showing completion step...');
        currentStep = 6;
        showStep(6);
        updateProgress();
        
        showMessage('onboarding-message', 'Setup completed successfully!', false);
        console.log('🎉 ONBOARDING COMPLETED SUCCESSFULLY!');
        
    } catch (error) {
        console.error('❌❌❌ ONBOARDING ERROR:', error);
        console.error('   Error name:', error.name);
        console.error('   Error message:', error.message);
        console.error('   Error stack:', error.stack);
        
        showMessage('onboarding-message', `Failed to complete setup: ${error.message}`, true);
    } finally {
        console.log('8️⃣ Hiding loading indicator...');
        showLoading('onboarding-loading', false);
    }
    
    console.log('🔵🔵🔵 completeOnboarding FUNCTION ENDED 🔵🔵🔵');
}

// Expose for debugging
window.debugOnboarding = {
    completeOnboarding,
    currentStep,
    totalSteps,
    showStep,
    checkAuth
};

console.log('🟢 onboarding.js fully loaded - debug tools available via window.debugOnboarding');
