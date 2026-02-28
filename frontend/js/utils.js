// Utility Functions

/**
 * Speak text using Google Cloud Text-to-Speech (with browser fallback)
 * @param {string} text - Text to speak
 * @param {string} lang - Language code (default: en-US)
 */
async function speakText(text, lang = 'en-US') {
    try {
        // Try Google Cloud TTS first (better quality)
        const response = await fetch('/api/speech/synthesize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                language: lang
            })
        });

        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            // Play the audio
            await audio.play();

            // Clean up URL after playing
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };

            return audio;
        } else {
            // Fallback to browser TTS
            console.warn('Google TTS failed, using browser fallback');
            return speakTextBrowser(text, lang);
        }
    } catch (error) {
        // Fallback to browser TTS on error
        console.warn('Google TTS error, using browser fallback:', error);
        return speakTextBrowser(text, lang);
    }
}

/**
 * Speak text using browser's speech synthesis (fallback)
 * @param {string} text - Text to speak
 * @param {string} lang - Language code (default: en-US)
 */
function speakTextBrowser(text, lang = 'en-US') {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 0.85; // Slower for accessibility
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        window.speechSynthesis.speak(utterance);
        return utterance;
    } else {
        console.warn('Speech synthesis not supported');
        return null;
    }
}

/**
 * Update status message on screen and announce it
 * @param {string} message - Message to display and announce
 * @param {boolean} speak - Whether to speak the message (default: true)
 */
function updateStatus(message, speak = true) {
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = message;
    }

    if (speak) {
        speakText(message);
    }

    console.log('Status:', message);
}

/**
 * Show/hide sections
 * @param {string} sectionId - ID of section to show
 * @param {boolean} show - Whether to show (true) or hide (false)
 */
function toggleSection(sectionId, show = true) {
    const section = document.getElementById(sectionId);
    if (section) {
        if (show) {
            section.classList.remove('hidden');
        } else {
            section.classList.add('hidden');
        }
    }
}

/**
 * Format distance for display
 * @param {number} meters - Distance in meters
 * @returns {string} Formatted distance string
 */
function formatDistance(meters) {
    if (meters < 1000) {
        return `${Math.round(meters)} meters`;
    } else {
        return `${(meters / 1000).toFixed(1)} kilometers`;
    }
}

/**
 * Format duration for display
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds} seconds`;
    } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        if (remainingSeconds === 0) {
            return `${minutes} minute${minutes > 1 ? 's' : ''}`;
        }
        return `${minutes} minute${minutes > 1 ? 's' : ''} ${remainingSeconds} seconds`;
    }
}

/**
 * Vibrate device if supported (for haptic feedback)
 * @param {number|number[]} pattern - Vibration pattern
 */
function vibrate(pattern = 200) {
    if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
    }
}

/**
 * Log to console with timestamp
 * @param {string} message - Message to log
 * @param {any} data - Optional data to log
 */
function log(message, data = null) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`, data || '');
}

/**
 * Handle errors and display user-friendly messages
 * @param {Error} error - Error object
 * @param {string} context - Context of the error
 */
function handleError(error, context = 'An error occurred') {
    console.error(`${context}:`, error);
    updateStatus(`Sorry, ${context.toLowerCase()}. Please try again.`, true);
    vibrate([100, 50, 100]); // Error vibration pattern
}

/**
 * Check if user is on mobile device
 * @returns {boolean}
 */
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Request microphone permission
 * @returns {Promise<boolean>}
 */
async function requestMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Stop immediately, just checking permission
        return true;
    } catch (error) {
        console.error('Microphone permission denied:', error);
        return false;
    }
}

// Export functions for use in other modules
window.utils = {
    speakText,
    speakTextBrowser,
    updateStatus,
    toggleSection,
    formatDistance,
    formatDuration,
    vibrate,
    log,
    handleError,
    isMobile,
    requestMicrophonePermission
};
