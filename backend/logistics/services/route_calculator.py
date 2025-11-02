import requests
import os
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class RouteCalculator:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTE_API_KEY')
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    
    def geocode_address(self, address: str) -> Tuple[float, float]:
        geocode_url = "https://api.openrouteservice.org/geocode/search"
        params = {
            'api_key': self.api_key,
            'text': address
        }
        
        try:
            response = requests.get(geocode_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['features']:
                coordinates = data['features'][0]['geometry']['coordinates']
                return coordinates[1], coordinates[0]
            else:
                raise Exception(f"No results found for address: {address}")
                
        except Exception as e:
            logger.error(f"Geocoding error for {address}: {str(e)}")
            raise Exception(f"Could not find location: {address}")
    
    def calculate_route(self, start_coords: Tuple[float, float], 
                       pickup_coords: Tuple[float, float], 
                       dropoff_coords: Tuple[float, float]) -> Dict:
        coordinates = [
            [start_coords[1], start_coords[0]],
            [pickup_coords[1], pickup_coords[0]],
            [dropoff_coords[1], dropoff_coords[0]]
        ]
        
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        body = {
            "coordinates": coordinates,
            "instructions": True,
            "geometry": True
        }
        
        try:
            response = requests.post(self.base_url, json=body, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            raise Exception("Route calculation failed. Please try again.")
    
    def parse_route_data(self, route_data: Dict) -> Dict:
        if not route_data or 'routes' not in route_data:
            raise Exception("Invalid route data received")
        
        route = route_data['routes'][0]
        summary = route['summary']
        
        distance_miles = summary['distance'] / 1609.34
        duration_hours = summary['duration'] / 3600
        
        geometry = self._encode_simple_polyline(route['geometry'])
        bounds = self._get_route_bounds(route['geometry'])
        
        return {
            'total_distance': round(distance_miles, 2),
            'total_duration': round(duration_hours, 2),
            'geometry': geometry,
            'segments': self._parse_segments(route['segments']),
            'waypoints': [
                {
                    'type': 'start', 
                    'coordinates': route_data['metadata']['query']['coordinates'][0]
                },
                {
                    'type': 'pickup', 
                    'coordinates': route_data['metadata']['query']['coordinates'][1]
                },
                {
                    'type': 'dropoff', 
                    'coordinates': route_data['metadata']['query']['coordinates'][2]
                }
            ],
            'bounds': bounds
        }
    
    def _encode_simple_polyline(self, geometry: Dict) -> str:
        coordinates = geometry['coordinates']
        return ';'.join([f"{coord[0]},{coord[1]}" for coord in coordinates])
    
    def _get_route_bounds(self, geometry: Dict) -> List:
        coordinates = geometry['coordinates']
        lats = [coord[1] for coord in coordinates]
        lngs = [coord[0] for coord in coordinates]
        
        return [
            [min(lats), min(lngs)],
            [max(lats), max(lngs)]
        ]
    
    def _parse_segments(self, segments: List) -> List:
        parsed_segments = []
        for segment in segments:
            parsed_segments.append({
                'distance': round(segment['distance'] / 1609.34, 2),
                'duration': round(segment['duration'] / 3600, 2),
                'steps': [
                    {
                        'instruction': step['instruction'],
                        'distance': round(step['distance'] / 1609.34, 2),
                        'duration': round(step['duration'] / 3600, 2)
                    }
                    for step in segment['steps']
                ]
            })
        return parsed_segments