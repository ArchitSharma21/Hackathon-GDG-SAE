"""
Location search service with fuzzy matching and natural language processing
"""
from typing import List, Dict, Optional
import json
import os
from difflib import SequenceMatcher
from backend.models.airport import AirportMap, AirportNode, LocationSearchResult

class LocationSearchService:
    """Service for searching airport locations"""

    def __init__(self, airport_data_path: str = None):
        """Initialize with airport map data"""
        if airport_data_path is None:
            # Default to hamburg_airport.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            airport_data_path = os.path.join(current_dir, '..', 'data', 'hamburg_airport.json')

        with open(airport_data_path, 'r') as f:
            data = json.load(f)
            self.airport_map = AirportMap(**data)

        # Create lookup dictionaries
        self.nodes_by_id = {node.id: node for node in self.airport_map.nodes}
        self.nodes_by_type = {}
        for node in self.airport_map.nodes:
            if node.type not in self.nodes_by_type:
                self.nodes_by_type[node.type] = []
            self.nodes_by_type[node.type].append(node)

    def search(self, query: str, max_results: int = 5) -> List[LocationSearchResult]:
        """
        Search for locations using fuzzy matching and natural language parsing

        Args:
            query: Search query (natural language or specific terms)
            max_results: Maximum number of results to return

        Returns:
            List of LocationSearchResult ordered by confidence
        """
        query_lower = query.lower().strip()

        # Parse natural language queries
        parsed_query = self._parse_natural_language(query_lower)

        results = []

        # Search by type first (if specified)
        if parsed_query['type']:
            nodes = self.nodes_by_type.get(parsed_query['type'], [])
            for node in nodes:
                confidence = 0.9  # High confidence for type matches
                results.append(LocationSearchResult(
                    id=node.id,
                    name=node.name,
                    type=node.type,
                    description=node.description,
                    confidence=confidence
                ))

        # Search by name/ID
        for node in self.airport_map.nodes:
            # Skip if already added by type search
            if any(r.id == node.id for r in results):
                continue

            # Calculate fuzzy match score
            name_score = self._fuzzy_match(query_lower, node.name.lower())
            id_score = self._fuzzy_match(query_lower, node.id.lower())
            type_score = self._fuzzy_match(query_lower, node.type.lower())

            # Take the best score
            best_score = max(name_score, id_score, type_score)

            # Only include if above threshold
            if best_score > 0.3:
                results.append(LocationSearchResult(
                    id=node.id,
                    name=node.name,
                    type=node.type,
                    description=node.description,
                    confidence=best_score
                ))

        # Sort by confidence (descending)
        results.sort(key=lambda x: x.confidence, reverse=True)

        return results[:max_results]

    def get_node_by_id(self, node_id: str) -> Optional[AirportNode]:
        """Get airport node by ID"""
        return self.nodes_by_id.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> List[AirportNode]:
        """Get all nodes of a specific type"""
        return self.nodes_by_type.get(node_type, [])

    def get_nearest_by_type(
        self,
        current_location: str,
        node_type: str
    ) -> Optional[AirportNode]:
        """
        Find nearest node of given type from current location
        (Simple implementation based on coordinate distance)
        """
        current_node = self.get_node_by_id(current_location)
        if not current_node:
            return None

        nodes = self.get_nodes_by_type(node_type)
        if not nodes:
            return None

        # Calculate distances (simple Euclidean)
        def distance(node):
            dx = node.coordinates.x - current_node.coordinates.x
            dy = node.coordinates.y - current_node.coordinates.y
            return (dx*dx + dy*dy) ** 0.5

        return min(nodes, key=distance)

    def _parse_natural_language(self, query: str) -> Dict[str, Optional[str]]:
        """
        Parse natural language query to extract intent

        Returns dict with:
            - type: location type (bathroom, gate, etc.)
            - gate_number: specific gate if mentioned
            - keywords: other relevant terms
        """
        result = {
            'type': None,
            'gate_number': None,
            'keywords': []
        }

        # Common terms for location types
        type_keywords = {
            'bathroom': ['bathroom', 'restroom', 'toilet', 'wc', 'lavatory'],
            'gate': ['gate', 'boarding'],
            'entrance': ['entrance', 'entry', 'door'],
            'exit': ['exit', 'way out', 'leave'],
            'security': ['security', 'checkpoint', 'screening'],
            'info': ['information', 'info desk', 'help desk', 'assistance'],
            'food': ['food', 'restaurant', 'cafe', 'dining', 'eat'],
            'restaurant': ['food', 'restaurant', 'cafe', 'dining', 'eat'],
            'stairs': ['stairs', 'escalator', 'elevator', 'floor'],
            'baggage': ['baggage', 'luggage', 'bags', 'claim']
        }

        # Check for type keywords
        for loc_type, keywords in type_keywords.items():
            if any(kw in query for kw in keywords):
                result['type'] = loc_type
                break

        # Extract gate number
        import re
        gate_match = re.search(r'gate\s*([a-z]?\d+)', query, re.IGNORECASE)
        if gate_match:
            gate_num = gate_match.group(1).lower()
            result['type'] = 'gate'
            result['gate_number'] = gate_num

        return result

    def _fuzzy_match(self, query: str, target: str) -> float:
        """
        Calculate fuzzy match score between query and target

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Exact match
        if query == target:
            return 1.0

        # Contains match
        if query in target or target in query:
            return 0.8

        # Sequence matcher for fuzzy matching
        return SequenceMatcher(None, query, target).ratio()


# Singleton instance
_location_service = None

def get_location_service() -> LocationSearchService:
    """Get or create LocationSearchService singleton"""
    global _location_service
    if _location_service is None:
        _location_service = LocationSearchService()
    return _location_service
