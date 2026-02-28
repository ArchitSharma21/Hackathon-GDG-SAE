// API Client for Airport Navigation Assistant

const API_BASE_URL = window.location.origin + '/api';

/**
 * API Client class
 */
class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    // Voice/Speech APIs

    /**
     * Transcribe audio to text
     * @param {Blob} audioBlob - Audio blob to transcribe
     * @returns {Promise<Object>} Transcription result
     */
    async transcribeAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);

        const response = await fetch(`${this.baseURL}/speech/transcribe`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Transcription failed: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Convert text to speech
     * @param {string} text - Text to synthesize
     * @param {string} language - Language code
     * @returns {Promise<Blob>} Audio blob
     */
    async synthesizeSpeech(text, language = 'en-US') {
        const response = await fetch(`${this.baseURL}/speech/synthesize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text, language })
        });

        if (!response.ok) {
            throw new Error(`Speech synthesis failed: ${response.status}`);
        }

        return await response.blob();
    }

    // Navigation APIs

    /**
     * Search for locations
     * @param {string} query - Search query
     * @returns {Promise<Object>} Search results
     */
    async searchLocations(query) {
        return await this.request(`/locations/search?query=${encodeURIComponent(query)}`);
    }

    /**
     * Get navigation route
     * @param {string} from - Starting location ID
     * @param {string} to - Destination location ID
     * @returns {Promise<Object>} Navigation route with turn-by-turn directions
     */
    async getNavigationRoute(from, to) {
        return await this.request('/navigation/route', {
            method: 'POST',
            body: JSON.stringify({
                from_location: from,
                to_location: to
            })
        });
    }

    // Flight APIs

    /**
     * Get flight status
     * @param {string} flightNumber - Flight number (e.g., LH123)
     * @returns {Promise<Object>} Flight information
     */
    async getFlightStatus(flightNumber) {
        return await this.request(`/flights/${flightNumber}`);
    }

    /**
     * Get user's flight information
     * @returns {Promise<Object>} User's flight details
     */
    async getMyFlight() {
        return await this.request('/flights/my-flight');
    }

    // Emergency APIs

    /**
     * Request emergency help
     * @param {string} currentLocation - Current location ID
     * @returns {Promise<Object>} Help response with nearest assistance location
     */
    async requestEmergencyHelp(currentLocation) {
        return await this.request('/emergency/help', {
            method: 'POST',
            body: JSON.stringify({
                current_location: currentLocation,
                emergency_type: 'help'
            })
        });
    }
}

// Create and export API client instance
const api = new APIClient();

window.api = api;
