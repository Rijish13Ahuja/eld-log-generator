from typing import Dict, List
import math

class ELDCalculator:
    def __init__(self):
        self.daily_driving_limit = 11
        self.daily_duty_limit = 14
        self.cycle_limit = 70
        self.break_required_after = 8
        self.break_duration = 0.5
        self.off_duty_required = 10
        self.fuel_stop_interval = 1000
    
    def calculate_eld_schedule(self, total_distance: float, total_duration: float, 
                             current_cycle_used: float) -> Dict:
        available_cycle_hours = self.cycle_limit - current_cycle_used
        available_daily_driving = min(self.daily_driving_limit, available_cycle_hours)
        
        estimated_driving_hours = total_duration
        days_needed = math.ceil(estimated_driving_hours / available_daily_driving)
        
        schedule = self._plan_schedule(total_distance, total_duration, available_daily_driving, days_needed)
        detailed_schedule = self.generate_detailed_schedule(schedule, current_cycle_used)
        
        return {
            'days_needed': days_needed,
            'available_cycle_hours': round(available_cycle_hours, 2),
            'available_daily_driving': round(available_daily_driving, 2),
            'schedule': detailed_schedule,
            'compliance_status': self._check_compliance(detailed_schedule, current_cycle_used)
        }
    
    def _plan_schedule(self, total_distance: float, total_duration: float, 
                      available_daily_driving: float, days_needed: int) -> List[Dict]:
        schedule = []
        remaining_distance = total_distance
        remaining_duration = total_duration
        
        for day in range(1, days_needed + 1):
            day_driving = min(available_daily_driving, remaining_duration)
            day_distance = (day_driving / remaining_duration) * remaining_distance
            
            breaks = self._plan_breaks(day_driving)
            fuel_stops = self._plan_fuel_stops(day_distance)
            
            day_schedule = {
                'day': day,
                'driving_time': round(day_driving, 2),
                'distance_covered': round(day_distance, 2),
                'breaks': breaks,
                'fuel_stops': fuel_stops,
                'total_on_duty_time': round(day_driving + sum(br['duration'] for br in breaks) + len(fuel_stops) * 0.5, 2)
            }
            
            schedule.append(day_schedule)
            
            remaining_distance -= day_distance
            remaining_duration -= day_driving
            
            if day < days_needed:
                schedule.append({
                    'day': day,
                    'type': 'off_duty',
                    'duration': self.off_duty_required,
                    'reason': 'Overnight rest'
                })
        
        return schedule
    
    def _plan_breaks(self, driving_time: float) -> List[Dict]:
        breaks = []
        
        if driving_time > self.break_required_after:
            breaks.append({
                'type': 'rest_break',
                'duration': self.break_duration,
                'reason': 'Required 30-minute break after 8 hours of driving'
            })
        
        return breaks
    
    def _plan_fuel_stops(self, distance: float) -> List[Dict]:
        fuel_stops = []
        fuel_stop_count = int(distance // self.fuel_stop_interval)
        
        for i in range(fuel_stop_count):
            fuel_stops.append({
                'type': 'fuel_stop',
                'duration': 0.5,
                'reason': f'Fuel stop #{i+1} (every 1000 miles)'
            })
        
        return fuel_stops
    
    def _check_compliance(self, schedule: List[Dict], current_cycle_used: float) -> Dict:
        total_driving = sum(day.get('driving_time', 0) for day in schedule if 'driving_time' in day)
        total_cycle_hours = current_cycle_used + total_driving
        
        return {
            'is_compliant': total_cycle_hours <= self.cycle_limit,
            'total_cycle_hours_used': round(total_cycle_hours, 2),
            'cycle_limit': self.cycle_limit,
            'remaining_cycle_hours': round(self.cycle_limit - total_cycle_hours, 2)
        }
    
    def generate_detailed_schedule(self, schedule: List[Dict], current_cycle_used: float) -> List[Dict]:
        detailed_days = []
        current_time = 8.0
        
        for day_schedule in schedule:
            if 'driving_time' in day_schedule:
                detailed_day = self._simulate_day_schedule(day_schedule, current_time)
                detailed_days.append(detailed_day)
                current_time = 8.0
            else:
                detailed_days.append(day_schedule)
        
        return detailed_days
    
    def _simulate_day_schedule(self, day_schedule: Dict, start_time: float) -> Dict:
        timeline = []
        current_time = start_time
        
        driving_segments = self._split_driving_time(day_schedule['driving_time'])
        
        for i, segment in enumerate(driving_segments):
            timeline.append({
                'type': 'driving',
                'start_time': current_time,
                'end_time': current_time + segment,
                'duration': segment,
                'description': f'Driving segment {i+1}'
            })
            current_time += segment
            
            cumulative_driving = sum(s['duration'] for s in timeline if s['type'] == 'driving')
            if cumulative_driving >= 8 and not any(s.get('break_added') for s in timeline):
                timeline.append({
                    'type': 'rest_break',
                    'start_time': current_time,
                    'end_time': current_time + 0.5,
                    'duration': 0.5,
                    'description': '30-minute rest break',
                    'break_added': True
                })
                current_time += 0.5
        
        for i, fuel_stop in enumerate(day_schedule['fuel_stops']):
            timeline.append({
                'type': 'fuel_stop',
                'start_time': current_time,
                'end_time': current_time + fuel_stop['duration'],
                'duration': fuel_stop['duration'],
                'description': f'Fuel stop {i+1}'
            })
            current_time += fuel_stop['duration']
        
        day_schedule['timeline'] = timeline
        day_schedule['total_on_duty_time'] = current_time - start_time
        
        return day_schedule
    
    def _split_driving_time(self, total_driving: float) -> List[float]:
        if total_driving <= 4:
            return [total_driving]
        elif total_driving <= 8:
            return [total_driving / 2, total_driving / 2]
        else:
            return [4, 4, total_driving - 8]