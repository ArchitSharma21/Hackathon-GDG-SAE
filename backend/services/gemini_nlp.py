"""
Gemini AI service for natural language understanding
Converts user queries into structured navigation commands
"""
import os
from typing import Optional, Dict, Any
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class GeminiNLPService:
    """Service for processing navigation queries with Gemini AI"""

    def __init__(self):
        """Initialize Gemini client"""
        if not GEMINI_AVAILABLE:
            print("[GEMINI] google-generativeai package not installed, using fallback only")
            self.model = None
            return

        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("[GEMINI] API key not set, using fallback only")
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("[GEMINI] Initialized successfully")
        except Exception as e:
            print(f"[GEMINI] Initialization failed: {e}, using fallback only")
            self.model = None

    def understand_navigation_query(self, user_query: str, available_locations: list = None) -> Dict[str, Any]:
        """
        Process natural language query and extract navigation intent

        Args:
            user_query: User's natural language query
            available_locations: List of available location types and IDs

        Returns:
            Dict with:
            - intent: navigation intent (find_location, go_to_gate, emergency, etc.)
            - location_type: type of location (bathroom, gate, restaurant, info, security, entrance)
            - location_id: specific location ID if mentioned (e.g., "gate_b12")
            - urgency: level of urgency (low, medium, high)
            - context: additional context from the query
        """

        # Build the prompt
        prompt = f"""You are an AI assistant for an airport navigation system helping visually impaired travelers.

Analyze this user query and extract navigation information:
User Query: "{user_query}"

Available location types in the airport:
- bathroom/restroom (IDs: bathroom_1, bathroom_2)
- gate (IDs: gate_a1, gate_a5, gate_b12, gate_b15, gate_b20)
- restaurant/food (ID: food_court)
- information desk (ID: info_desk)
- security checkpoint (ID: security)
- entrance (ID: entrance)

Extract and return a JSON object with these fields:
{{
    "intent": "find_location" | "go_to_gate" | "emergency" | "general_info",
    "location_type": "bathroom" | "gate" | "restaurant" | "info" | "security" | "entrance" | "unknown",
    "location_id": "specific_id_if_mentioned" or null,
    "urgency": "low" | "medium" | "high",
    "context": "brief summary of what user wants",
    "search_query": "simplified search term for the location search system"
}}

Examples:
- "I need to use the restroom urgently" → {{"intent": "find_location", "location_type": "bathroom", "location_id": null, "urgency": "high", "context": "urgent bathroom need", "search_query": "bathroom"}}
- "Where is gate B12?" → {{"intent": "go_to_gate", "location_type": "gate", "location_id": "gate_b12", "urgency": "medium", "context": "looking for gate B12", "search_query": "gate b12"}}
- "I'm hungry, where can I eat?" → {{"intent": "find_location", "location_type": "restaurant", "location_id": null, "urgency": "low", "context": "looking for food", "search_query": "restaurant"}}
- "Help! I need assistance" → {{"intent": "emergency", "location_type": "info", "location_id": null, "urgency": "high", "context": "emergency assistance needed", "search_query": "info desk"}}
- "Where can I wash my hands?" → {{"intent": "find_location", "location_type": "bathroom", "location_id": null, "urgency": "low", "context": "looking for bathroom to wash hands", "search_query": "bathroom"}}

Return ONLY the JSON object, no other text.
"""

        # If Gemini not available, use fallback immediately
        if not self.model:
            return self._fallback_parse(user_query)

        try:
            # Generate response
            response = self.model.generate_content(prompt)

            # Extract JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Parse JSON
            result = json.loads(response_text)

            print(f"[GEMINI] Query: '{user_query}' → Intent: {result.get('intent')}, Type: {result.get('location_type')}, ID: {result.get('location_id')}")

            return result

        except json.JSONDecodeError as e:
            print(f"[GEMINI] Failed to parse JSON: {e}")
            print(f"[GEMINI] Raw response: {response_text}")
            # Fallback to simple parsing
            return self._fallback_parse(user_query)

        except Exception as e:
            print(f"[GEMINI] Error: {e}")
            # Fallback to simple parsing
            return self._fallback_parse(user_query)

    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Simple fallback parser if Gemini fails"""
        q = query.lower()

        result = {
            "intent": "find_location",
            "location_type": "unknown",
            "location_id": None,
            "urgency": "medium",
            "context": query,
            "search_query": query
        }

        # Simple keyword matching
        if any(word in q for word in ['bathroom', 'restroom', 'toilet', 'wc', 'wash', 'pee', 'poop', 'lavatory', 'loo']):
            result["location_type"] = "bathroom"
            result["search_query"] = "bathroom"
            result["urgency"] = "high"  # Bathroom needs are often urgent
        elif any(word in q for word in ['gate', 'boarding']):
            result["location_type"] = "gate"
            result["search_query"] = "gate"
            # Try to extract gate number
            import re
            match = re.search(r'gate[\s]*([a-e])\s*(\d+)', q, re.IGNORECASE)
            if match:
                result["location_id"] = f"gate_{match.group(1).lower()}{match.group(2)}"
                result["search_query"] = f"gate {match.group(1)}{match.group(2)}"
        elif any(word in q for word in ['food', 'eat', 'restaurant', 'hungry', 'cafe']):
            result["location_type"] = "restaurant"
            result["search_query"] = "food"
        elif any(word in q for word in ['help', 'emergency', 'assist', 'info']):
            result["intent"] = "emergency" if any(word in q for word in ['help', 'emergency']) else "find_location"
            result["location_type"] = "info"
            result["search_query"] = "info desk"
        elif any(word in q for word in ['security', 'checkpoint']):
            result["location_type"] = "security"
            result["search_query"] = "security"
        elif any(word in q for word in ['entrance', 'exit']):
            result["location_type"] = "entrance"
            result["search_query"] = "entrance"

        # Check urgency
        if any(word in q for word in ['urgent', 'quickly', 'hurry', 'emergency', 'fast', 'asap']):
            result["urgency"] = "high"

        return result


# Singleton instance
_gemini_service = None

def get_gemini_service() -> GeminiNLPService:
    """Get or create GeminiNLPService singleton"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiNLPService()
    return _gemini_service
