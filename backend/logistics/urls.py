from django.urls import path
from . import views

urlpatterns = [
    path('calculate-route/', views.calculate_route, name='calculate_route'),
    path('health/', views.health_check, name='health_check'),
    path('demo/', views.demo_route, name='demo_route'),
]