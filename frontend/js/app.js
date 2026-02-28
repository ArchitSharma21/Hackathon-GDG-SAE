// Main Application Logic

class AirportNavigationApp {
    constructor() {
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        console.log('Airport Navigation Assistant initializing...');

        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    /**
     * Setup event listeners and initial state
     */
    setup() {
        // Listen for position updates from simulation
        window.addEventListener('message', (event) => {
            if (event.data.type === 'position_update') {
                this.handlePositionUpdate(event.data);
            }
        });

        // Voice button
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                window.voiceController.startListening();
            });
        }

        // Navigation buttons
        const nextStepBtn = document.getElementById('next-step-btn');
        if (nextStepBtn) {
            nextStepBtn.addEventListener('click', () => {
                window.navigationController.nextStep();
            });
        }

        const cancelNavBtn = document.getElementById('cancel-nav-btn');
        if (cancelNavBtn) {
            cancelNavBtn.addEventListener('click', () => {
                window.navigationController.cancelNavigation();
            });
        }

        // Emergency button
        const emergencyBtn = document.getElementById('emergency-btn');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => {
                this.handleEmergency();
            });
        }

        // Quick action buttons
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                if (query) {
                    window.voiceController.handleVoiceCommand(query);
                }
            });
        });

        // Navigate to gate button
        const navigateToGateBtn = document.getElementById('navigate-to-gate-btn');
        if (navigateToGateBtn) {
            navigateToGateBtn.addEventListener('click', () => {
                const gate = document.getElementById('flight-gate').textContent;
                if (gate && gate !== '---') {
                    const gateId = gate.toLowerCase().replace(/\s+/g, '_').replace(/^/, 'gate_');
                    window.navigationController.startNavigation(
                        window.navigationController.currentLocation,
                        gateId
                    );
                }
            });
        }

        // Request microphone permission on first interaction
        document.addEventListener('click', () => {
            this.requestPermissions();
        }, { once: true });

        // Welcome message
        this.welcome();

        console.log('Airport Navigation Assistant ready!');
    }

    /**
     * Welcome message
     */
    welcome() {
        const welcomeMessage = 'Welcome to Hamburg Airport Navigation Assistant. I can help you find gates, bathrooms, and other facilities. Tap the microphone to begin, or use the quick action buttons below.';
        utils.updateStatus(welcomeMessage, true);
    }

    /**
     * Request necessary permissions
     */
    async requestPermissions() {
        try {
            const micPermission = await utils.requestMicrophonePermission();
            if (!micPermission) {
                console.warn('Microphone permission not granted');
            }
        } catch (error) {
            console.error('Permission request failed:', error);
        }
    }

    /**
     * Show flight information
     */
    async showFlightInfo() {
        try {
            utils.updateStatus('Fetching your flight information...', true);

            const flightData = await api.getMyFlight();

            if (flightData) {
                document.getElementById('flight-number').textContent = flightData.flight_number || '---';
                document.getElementById('flight-gate').textContent = flightData.gate || '---';
                document.getElementById('flight-status').textContent = flightData.status || '---';
                document.getElementById('flight-time').textContent = flightData.departure_time || '---';

                utils.toggleSection('flight-section', true);

                if (flightData.gate && flightData.gate !== '---') {
                    utils.toggleSection('navigate-to-gate-btn', true);
                }

                const message = `Your flight ${flightData.flight_number} departs from gate ${flightData.gate} at ${flightData.departure_time}. Status: ${flightData.status}`;
                utils.updateStatus(message, true);
            }
        } catch (error) {
            utils.handleError(error, 'Failed to fetch flight information');
        }
    }

    /**
     * Handle position update from simulation
     */
    handlePositionUpdate(data) {
        console.log('Position update received:', data);

        // Update current location in navigation controller
        if (window.navigationController && data.location) {
            window.navigationController.setCurrentLocation(data.location);

            // Update status with location info
            const message = `You are at ${data.name} (Floor ${data.floor})`;
            document.getElementById('status-text').textContent = message;
        }
    }

    /**
     * Handle emergency help request
     */
    async handleEmergency() {
        try {
            utils.updateStatus('Requesting emergency assistance...', true);
            utils.vibrate([200, 100, 200, 100, 200, 100, 200]); // Emergency vibration

            const response = await api.requestEmergencyHelp(
                window.navigationController.currentLocation
            );

            if (response) {
                utils.updateStatus(response.message, true);

                // Navigate to help desk
                if (response.nearest_help) {
                    await window.navigationController.startNavigation(
                        window.navigationController.currentLocation,
                        response.nearest_help
                    );
                }
            }
        } catch (error) {
            utils.handleError(error, 'Emergency request failed');
        }
    }
}

// Initialize app
window.app = new AirportNavigationApp();
