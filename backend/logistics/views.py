from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import TripInputSerializer
from .services.route_calculator import RouteCalculator
from .services.eld_calculator import ELDCalculator
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def calculate_route(request):
    serializer = TripInputSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            route_calculator = RouteCalculator()
            eld_calculator = ELDCalculator()
            
            current_coords = route_calculator.geocode_address(serializer.validated_data['current_location'])
            pickup_coords = route_calculator.geocode_address(serializer.validated_data['pickup_location'])
            dropoff_coords = route_calculator.geocode_address(serializer.validated_data['dropoff_location'])
            
            route_data = route_calculator.calculate_route(current_coords, pickup_coords, dropoff_coords)
            parsed_route = route_calculator.parse_route_data(route_data)
            
            eld_schedule = eld_calculator.calculate_eld_schedule(
                parsed_route['total_distance'],
                parsed_route['total_duration'],
                serializer.validated_data['current_cycle_used']
            )
            
            response_data = {
                'status': 'success',
                'trip_summary': {
                    'total_distance': parsed_route['total_distance'],
                    'total_duration': parsed_route['total_duration'],
                    'route_geometry': parsed_route['geometry'],
                    'waypoints': parsed_route['waypoints'],
                    'bounds': parsed_route.get('bounds', [])
                },
                'eld_schedule': eld_schedule,
                'compliance': eld_schedule['compliance_status']
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def health_check(request):
    return JsonResponse({
        'status': 'success', 
        'message': 'Backend is running!',
        'service': 'ELD Log Generator API'
    })

@api_view(['GET'])
def demo_route(request):
    demo_data = {
        'status': 'success',
        'trip_summary': {
            'total_distance': 225.5,
            'total_duration': 4.2,
            'route_geometry': "-74.0060,40.7128;-75.1652,39.9526;-77.0369,38.9072",
            'waypoints': [
                {'type': 'start', 'coordinates': [-74.0060, 40.7128]},
                {'type': 'pickup', 'coordinates': [-75.1652, 39.9526]},
                {'type': 'dropoff', 'coordinates': [-77.0369, 38.9072]}
            ],
            'bounds': [[38.9072, -77.0369], [40.7128, -74.0060]]
        },
        'eld_schedule': {
            'days_needed': 1,
            'available_cycle_hours': 50.0,
            'available_daily_driving': 11.0,
            'schedule': [
                {
                    'day': 1,
                    'driving_time': 4.2,
                    'distance_covered': 225.5,
                    'breaks': [
                        {
                            'type': 'rest_break',
                            'duration': 0.5,
                            'reason': 'Required 30-minute break after 8 hours of driving'
                        }
                    ],
                    'fuel_stops': [],
                    'total_on_duty_time': 4.7,
                    'timeline': [
                        {
                            'type': 'driving',
                            'start_time': 8.0,
                            'end_time': 12.2,
                            'duration': 4.2,
                            'description': 'Driving segment 1'
                        }
                    ]
                }
            ],
            'compliance_status': {
                'is_compliant': True,
                'total_cycle_hours_used': 24.2,
                'cycle_limit': 70,
                'remaining_cycle_hours': 45.8
            }
        }
    }
    return JsonResponse(demo_data)