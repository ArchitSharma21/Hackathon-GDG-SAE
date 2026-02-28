// Voice Interface Controller

class VoiceController {
    constructor() {
        this.isListening = false;
        this.recognition = null;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.audioChunks = [];

        this.initSpeechRecognition();
    }

    /**
     * Initialize Web Speech API for recognition
     */
    initSpeechRecognition() {
        // Check if browser supports Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                console.log('Voice recognition started');
                this.isListening = true;
                this.updateListeningUI(true);
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const confidence = event.results[0][0].confidence;
                console.log('Recognized:', transcript, 'Confidence:', confidence);

                this.handleVoiceCommand(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                utils.handleError(new Error(event.error), 'Voice recognition error');
                this.stopListening();
            };

            this.recognition.onend = () => {
                console.log('Voice recognition ended');
                this.stopListening();
            };
        } else {
            console.warn('Web Speech API not supported in this browser');
        }
    }

    /**
     * Start listening for voice input
     */
    startListening() {
        if (!this.recognition) {
            utils.updateStatus('Voice recognition is not supported in your browser', true);
            return;
        }

        if (this.isListening) {
            this.stopListening();
            return;
        }

        try {
            this.recognition.start();
            utils.vibrate(100); // Haptic feedback
        } catch (error) {
            console.error('Failed to start recognition:', error);
            utils.handleError(error, 'Failed to start voice recognition');
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        this.isListening = false;
        this.updateListeningUI(false);
    }

    /**
     * Update UI to reflect listening state
     */
    updateListeningUI(listening) {
        const voiceBtn = document.getElementById('voice-btn');
        const listeningIndicator = document.getElementById('listening-indicator');

        if (voiceBtn) {
            if (listening) {
                voiceBtn.classList.add('listening');
                voiceBtn.querySelector('.voice-label').textContent = 'Listening...';
            } else {
                voiceBtn.classList.remove('listening');
                voiceBtn.querySelector('.voice-label').textContent = 'Tap to Speak';
            }
        }

        if (listeningIndicator) {
            listeningIndicator.textContent = listening ? 'Listening...' : '';
        }
    }

    /**
     * Handle voice command
     */
    async handleVoiceCommand(command) {
        const lowerCommand = command.toLowerCase();
        utils.log('Processing voice command:', command);

        // Update status to show what was heard
        utils.updateStatus(`You said: "${command}"`, false);

        // Navigation-related commands
        if (lowerCommand.includes('bathroom') || lowerCommand.includes('restroom') || lowerCommand.includes('toilet')) {
            await window.navigationController.searchAndNavigate('bathroom');
        }
        // Gate commands
        else if (lowerCommand.includes('gate')) {
            const gateMatch = lowerCommand.match(/gate\s*([a-z]?\d+)/i);
            if (gateMatch) {
                const gateName = `gate_${gateMatch[1].toLowerCase().replace(/\s/g, '')}`;
                await window.navigationController.searchAndNavigate(gateName);
            } else {
                utils.updateStatus('Which gate would you like to find?', true);
            }
        }
        // Information desk
        else if (lowerCommand.includes('information') || lowerCommand.includes('info desk') || lowerCommand.includes('help desk')) {
            await window.navigationController.searchAndNavigate('info_desk');
        }
        // Food court
        else if (lowerCommand.includes('food') || lowerCommand.includes('restaurant') || lowerCommand.includes('eat')) {
            await window.navigationController.searchAndNavigate('food_court');
        }
        // Flight information
        else if (lowerCommand.includes('flight') || lowerCommand.includes('my flight')) {
            await window.app.showFlightInfo();
        }
        // Emergency
        else if (lowerCommand.includes('help') || lowerCommand.includes('emergency') || lowerCommand.includes('assist')) {
            await window.app.handleEmergency();
        }
        // Next step in navigation
        else if (lowerCommand.includes('next') || lowerCommand.includes('continue')) {
            if (window.navigationController.currentRoute) {
                window.navigationController.nextStep();
            } else {
                utils.updateStatus('No active navigation. How can I help you?', true);
            }
        }
        // Cancel navigation
        else if (lowerCommand.includes('cancel') || lowerCommand.includes('stop navigation')) {
            window.navigationController.cancelNavigation();
        }
        // General location search
        else if (lowerCommand.includes('where is') || lowerCommand.includes('find') || lowerCommand.includes('locate')) {
            await window.navigationController.searchAndNavigate(command);
        }
        // Default: try general search
        else {
            utils.updateStatus('I didn\'t understand that. Try asking "Where is the bathroom?" or "Find gate B12"', true);
        }
    }

    /**
     * Speak text using browser's speech synthesis
     */
    speak(text, lang = 'en-US') {
        return utils.speakText(text, lang);
    }
}

// Initialize voice controller
window.voiceController = new VoiceController();
