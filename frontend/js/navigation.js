// Navigation Controller

class NavigationController {
    constructor() {
        this.currentRoute = null;
        this.currentStepIndex = 0;
        this.currentLocation = 'entrance'; // Default starting location
    }

    /**
     * Search for a location and navigate to it
     */
    async searchAndNavigate(query) {
        try {
            utils.updateStatus(`Searching for ${query}...`, true);

            const results = await api.searchLocations(query);

            if (results && results.results && results.results.length > 0) {
                const destination = results.results[0];
                await this.startNavigation(this.currentLocation, destination.id);
            } else {
                utils.updateStatus(`Sorry, I couldn't find "${query}". Please try again.`, true);
            }
        } catch (error) {
            utils.handleError(error, 'Failed to search for location');
        }
    }

    /**
     * Start navigation from current location to destination
     */
    async startNavigation(from, to) {
        try {
            utils.updateStatus('Calculating route...', true);

            const route = await api.getNavigationRoute(from, to);

            if (route && route.steps && route.steps.length > 0) {
                this.currentRoute = route;
                this.currentStepIndex = 0;

                this.showNavigationSection();
                this.displayCurrentStep();

                utils.vibrate([100, 50, 100]); // Success vibration
            } else {
                utils.updateStatus('Unable to find a route to that location', true);
            }
        } catch (error) {
            utils.handleError(error, 'Failed to get navigation route');
        }
    }

    /**
     * Display current navigation step
     */
    displayCurrentStep() {
        if (!this.currentRoute || this.currentStepIndex >= this.currentRoute.steps.length) {
            this.arriveAtDestination();
            return;
        }

        const step = this.currentRoute.steps[this.currentStepIndex];

        // Update UI
        document.getElementById('step-num').textContent = step.step_number;
        document.getElementById('step-text').textContent = step.instruction;
        document.getElementById('step-distance').textContent = utils.formatDistance(step.distance);

        // Announce the step
        const announcement = `Step ${step.step_number}. ${step.instruction}. Distance: ${utils.formatDistance(step.distance)}`;
        utils.speakText(announcement);

        utils.log('Navigation step:', step);
    }

    /**
     * Move to next navigation step
     */
    nextStep() {
        if (!this.currentRoute) {
            utils.updateStatus('No active navigation', true);
            return;
        }

        this.currentStepIndex++;

        if (this.currentStepIndex < this.currentRoute.steps.length) {
            this.displayCurrentStep();
            utils.vibrate(100); // Step advancement feedback
        } else {
            this.arriveAtDestination();
        }
    }

    /**
     * Handle arrival at destination
     */
    arriveAtDestination() {
        if (!this.currentRoute) return;

        const destination = this.currentRoute.to_location;
        const message = `You have arrived at ${destination}`;

        utils.updateStatus(message, true);
        utils.vibrate([200, 100, 200, 100, 200]); // Arrival vibration pattern

        // Update current location
        this.currentLocation = this.currentRoute.to_location;

        // Clear navigation after a delay
        setTimeout(() => {
            this.cancelNavigation();
        }, 5000);
    }

    /**
     * Cancel current navigation
     */
    cancelNavigation() {
        this.currentRoute = null;
        this.currentStepIndex = 0;

        this.hideNavigationSection();
        utils.updateStatus('Navigation cancelled. How can I help you?', true);
        utils.vibrate(200);
    }

    /**
     * Show navigation section
     */
    showNavigationSection() {
        utils.toggleSection('navigation-section', true);
    }

    /**
     * Hide navigation section
     */
    hideNavigationSection() {
        utils.toggleSection('navigation-section', false);
    }

    /**
     * Set current location (for simulated positioning)
     */
    setCurrentLocation(locationId) {
        this.currentLocation = locationId;
        utils.log('Current location updated:', locationId);
    }
}

// Initialize navigation controller
window.navigationController = new NavigationController();
