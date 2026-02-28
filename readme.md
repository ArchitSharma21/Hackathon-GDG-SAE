# Airport Navigation Assistant

A voice-driven Progressive Web App (PWA) designed to help visually impaired travelers navigate Hamburg Airport with ease. Built for accessibility and independence.

## Features

- **Voice-First Interface**: Natural language voice commands for all functionality
- **Turn-by-Turn Navigation**: Audio-guided directions to gates, bathrooms, and facilities
- **Flight Information**: Real-time flight status via Lufthansa API integration
- **Emergency Assistance**: Quick access to help desks and information centers
- **High Accessibility**: WCAG 2.1 Level AA compliant with high contrast, large text, and screen reader support
- **Offline Capable**: PWA with service worker for basic offline functionality

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Cloud account with Speech-to-Text and Text-to-Speech APIs enabled
- Lufthansa API credentials
- Modern web browser (Chrome, Firefox, Safari)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Hackathon-GDG-SAE
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure Google Cloud credentials**
   - Download your service account JSON key from Google Cloud Console
   - Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env` with the path to your key file

5. **Configure Lufthansa API**
   - Add your `LUFTHANSA_CLIENT_ID` and `LUFTHANSA_CLIENT_SECRET` to `.env`

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python main.py
   ```

   The server will start on `http://localhost:8000`

2. **Access the PWA**
   - Open your browser and navigate to `http://localhost:8000`
   - The PWA will be served automatically
   - Install the PWA on mobile for the best experience

### Development

#### Backend Structure

```
backend/
├── main.py              # FastAPI application entry point
├── routers/             # API route handlers
│   ├── speech.py       # Google Cloud Speech/TTS endpoints
│   ├── navigation.py   # Location search and routing
│   ├── flights.py      # Lufthansa API integration
│   └── emergency.py    # Emergency help endpoints
├── services/           # Business logic services
├── models/             # Pydantic data models
└── data/               # Airport map data (JSON)
```

#### Frontend Structure

```
frontend/
├── index.html          # Main PWA page
├── manifest.json       # PWA manifest
├── service-worker.js   # Offline caching
├── styles/
│   └── main.css       # Accessible, high-contrast styles
└── js/
    ├── app.js         # Main application logic
    ├── voice.js       # Voice interface controller
    ├── navigation.js  # Navigation state management
    ├── api.js         # API client
    └── utils.js       # Utility functions
```

## Usage

### Voice Commands

- **Find locations**: "Where is gate B12?", "Find the nearest bathroom"
- **Navigation**: "Navigate to gate A5", "Take me to the food court"
- **Flight info**: "What gate is my flight?", "Show flight LH123"
- **Emergency**: "I need help", "Emergency assistance"
- **Control**: "Next step", "Cancel navigation"

### Quick Actions

The app includes quick action buttons for common tasks:
- Find Bathroom
- My Flight
- Info Desk

### Navigation

1. Tap the microphone or use a voice command
2. Ask for a location (e.g., "Where is gate B12?")
3. The app will calculate a route and begin turn-by-turn guidance
4. Tap "Next Step" or say "Next" to advance through directions
5. Arrive at your destination with audio confirmation

## Testing

### Manual Testing Checklist

- [ ] Voice input/output works correctly
- [ ] Location search finds relevant results
- [ ] Navigation provides clear turn-by-turn directions
- [ ] Flight information displays correctly
- [ ] Emergency button triggers help
- [ ] PWA installs on mobile device
- [ ] Offline mode works for basic navigation

### Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Safari (iOS/macOS)
- ✅ Firefox
- ⚠️ Web Speech API required for voice features

## Accessibility

This application is designed with accessibility as the primary focus:

- **Voice-first interaction**: All features accessible via voice
- **High contrast mode**: 4.5:1 minimum contrast ratio
- **Large touch targets**: Minimum 44x44px for all interactive elements
- **Screen reader compatible**: Proper ARIA labels and semantic HTML
- **No time constraints**: User-controlled navigation progression
- **Haptic feedback**: Vibration patterns for key events

## API Documentation

### Endpoints

**Health Check**
```
GET /api/health
```

**Speech Recognition**
```
POST /api/speech/transcribe
Content-Type: multipart/form-data
Body: audio file
```

**Text-to-Speech**
```
POST /api/speech/synthesize
Content-Type: application/json
Body: { "text": "Hello", "language": "en-US" }
```

**Location Search**
```
GET /api/locations/search?query=bathroom
```

**Navigation Route**
```
POST /api/navigation/route
Content-Type: application/json
Body: { "from_location": "entrance", "to_location": "gate_b12" }
```

**Flight Status**
```
GET /api/flights/LH123
```

**Emergency Help**
```
POST /api/emergency/help
Content-Type: application/json
Body: { "current_location": "entrance" }
```

## Airport Map Data

The Hamburg Airport map is stored in `backend/data/hamburg_airport.json` with:
- **Nodes**: Physical locations (gates, bathrooms, entrances, etc.)
- **Paths**: Connections between nodes with directions and distances

To add new locations or modify the layout, edit this JSON file.

## Deployment

### Production Deployment

1. **Configure environment variables** for production
2. **Set CORS origins** in `backend/main.py` to your domain
3. **Deploy backend** to a cloud platform (e.g., Render, Railway, Google Cloud Run)
4. **Deploy frontend** as static files (can be served by backend)
5. **Configure HTTPS** (required for PWA features like microphone access)

### Recommended Platforms

- **Backend**: Google Cloud Run, Render, Railway
- **Frontend**: Vercel, Netlify (or served from backend)
- **Combined**: Single deployment with FastAPI serving frontend

## Contributing

This project was built for the GDG SAE Hackathon 2026. Contributions are welcome!

## License

[Add your license here]

## Acknowledgments

- Google Cloud Speech & Text-to-Speech APIs
- Lufthansa OpenAPI for flight data
- Hamburg Airport for inspiration
- Built with accessibility and inclusion in mind

## Support

For issues or questions, please create an issue in the repository.

---

**Built with ❤️ for accessibility and independence**
