"""
Pathfinding service using Dijkstra's algorithm for airport navigation
"""
from typing import List, Dict, Optional, Tuple
import heapq
from backend.models.airport import AirportMap, AirportPath, AirportNode
from backend.models.navigation import NavigationStep, NavigationRoute
from backend.services.location_search import get_location_service

class PathfindingService:
    """Service for finding optimal routes in the airport"""

    def __init__(self):
        """Initialize with airport map data"""
        self.location_service = get_location_service()
        self.airport_map = self.location_service.airport_map

        # Build graph structure
        self.graph = self._build_graph()

    def _build_graph(self) -> Dict[str, List[Tuple[str, float, str]]]:
        """
        Build adjacency list graph from airport paths

        Returns:
            Dict mapping node_id to list of (neighbor_id, distance, directions)
        """
        graph = {node.id: [] for node in self.airport_map.nodes}

        # Add edges (bidirectional for most paths)
        for path in self.airport_map.paths:
            from_node = path.from_node
            to_node = path.to

            # Add forward edge
            graph[from_node].append((to_node, path.distance, path.directions))

            # Add reverse edge (bidirectional)
            reverse_directions = self._reverse_directions(path.directions)
            graph[to_node].append((from_node, path.distance, reverse_directions))

        return graph

    def _reverse_directions(self, directions: str) -> str:
        """Generate reverse directions (simple heuristic)"""
        # For MVP, create simple reverse direction
        return f"Turn around and go back: {directions}"

    def find_route(
        self,
        from_location: str,
        to_location: str
    ) -> Optional[NavigationRoute]:
        """
        Find optimal route using Dijkstra's algorithm

        Args:
            from_location: Starting location ID
            to_location: Destination location ID

        Returns:
            NavigationRoute with turn-by-turn steps, or None if no path exists
        """
        # Validate locations exist
        from_node = self.location_service.get_node_by_id(from_location)
        to_node = self.location_service.get_node_by_id(to_location)

        if not from_node or not to_node:
            return None

        # Run Dijkstra's algorithm
        path_info = self._dijkstra(from_location, to_location)

        if not path_info:
            return None

        path, total_distance = path_info

        # Convert path to navigation steps
        steps = self._path_to_steps(path)

        # Calculate total duration (assuming average walking speed of 1.4 m/s)
        total_duration = int(total_distance / 1.4)

        return NavigationRoute(
            from_location=from_node.name,
            to_location=to_node.name,
            total_distance=total_distance,
            total_duration=total_duration,
            steps=steps,
            current_step=0
        )

    def _dijkstra(
        self,
        start: str,
        end: str
    ) -> Optional[Tuple[List[Tuple[str, str, float]], float]]:
        """
        Dijkstra's algorithm for shortest path

        Returns:
            Tuple of (path_with_directions, total_distance) or None
            path_with_directions is list of (node_id, directions, distance)
        """
        # Priority queue: (distance, node_id)
        pq = [(0, start)]

        # Track distances and previous nodes
        distances = {start: 0}
        previous = {}
        directions_map = {}

        visited = set()

        while pq:
            current_dist, current = heapq.heappop(pq)

            if current in visited:
                continue

            visited.add(current)

            # Found destination
            if current == end:
                # Reconstruct path
                path = []
                total_distance = distances[end]
                node = end

                while node != start:
                    prev_node = previous[node]
                    directions = directions_map.get((prev_node, node), "Continue")
                    # Find edge distance
                    edge_dist = 0
                    for neighbor, dist, _ in self.graph[prev_node]:
                        if neighbor == node:
                            edge_dist = dist
                            break

                    path.append((node, directions, edge_dist))
                    node = prev_node

                path.append((start, "Starting point", 0))
                path.reverse()

                return (path, total_distance)

            # Explore neighbors
            for neighbor, distance, directions in self.graph.get(current, []):
                new_distance = current_dist + distance

                if neighbor not in distances or new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
                    directions_map[(current, neighbor)] = directions
                    heapq.heappush(pq, (new_distance, neighbor))

        # No path found
        return None

    def _path_to_steps(
        self,
        path: List[Tuple[str, str, float]]
    ) -> List[NavigationStep]:
        """
        Convert path to navigation steps

        Args:
            path: List of (node_id, directions, distance)

        Returns:
            List of NavigationStep objects
        """
        steps = []

        for i, (node_id, directions, distance) in enumerate(path[1:], 1):
            # Get node info
            node = self.location_service.get_node_by_id(node_id)
            prev_node = self.location_service.get_node_by_id(path[i-1][0])

            if not node or not prev_node:
                continue

            # Calculate duration (walking speed ~1.4 m/s)
            duration = int(distance / 1.4)

            # Create step
            step = NavigationStep(
                step_number=i,
                instruction=directions,
                distance=distance,
                duration=duration,
                from_location=prev_node.name,
                to_location=node.name
            )

            steps.append(step)

        return steps


# Singleton instance
_pathfinding_service = None

def get_pathfinding_service() -> PathfindingService:
    """Get or create PathfindingService singleton"""
    global _pathfinding_service
    if _pathfinding_service is None:
        _pathfinding_service = PathfindingService()
    return _pathfinding_service
