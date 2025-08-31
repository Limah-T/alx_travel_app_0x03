from django.urls import path
from .views import UserViewset, LoginViewset, PropertyViewset, BookingViewset, payment_view

urlpatterns = [
    path('register/', UserViewset.as_view({'post': 'create'}), name='register'),
    path('login/', LoginViewset.as_view({'post': 'create'}), name='login'),
    path('users/', UserViewset.as_view({'get': 'list'}), name='users'),
    path('property/', PropertyViewset.as_view({'post': 'create', 'get': 'list'}), name='property'),
    path('property/<str:pk>', PropertyViewset.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'})),
    path('booking/', BookingViewset.as_view({'post': 'create', 'get': 'list'}), name='booking'),
    path('booking/<str:pk>', BookingViewset.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'}), name='booking'),
    path('payment/<str:pk>', payment_view, name='payment'),
]