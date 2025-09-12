from .serializers import PropertySerializer, BookingSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.cache import cache

from datetime import datetime
from .utils.helper_functions import check_if_is_admin, check_single_user_in_cache_db
from .models import Property, Booking, Payment
from .tasks import email_verification
from .models import Property, Booking, Review
import requests, os, uuid

class PropertyViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "put", "delete"]
    serializer_class = PropertySerializer

    def get_queryset(self):
        properties = cache.get("properties")
        if not properties:
            all_properties = list(Property.objects.values('property_id', 'name', 'description', 'location', 'pricepernight'))
            cache.set(properties)
        return 

    def create(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({"error": "User not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
        if user.role == "guest":
            return Response({"error": "You cannot perform this account with a guest acccount, fill the host form to upgrade your account."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name']
        description = serializer.validated_data['description']
        location = serializer.validated_data['location']
        pricepernight = serializer.validated_data['pricepernight']
        # property = Property.objects.create(
        #                         user=get_user, name=name,
        #                         description=description, 
        #                         location=location, pricepernight=pricepernight)
        # serializer = self.serializer_class(property)
        print(serializer.data)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        print(request.user.role)
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        print(kwargs.get('pk'))
        property = get_object_or_404(Property, property_id=kwargs.get('pk'))
        serializer = self.get_serializer(property)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        property = get_object_or_404(Property, property_id=kwargs.get('pk'))
        serializer = self.get_serializer(data=request.data, instance=property, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(property)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def destroy(self, request, *args, **kwargs):
        property = get_object_or_404(Property, property_id=kwargs.get('pk'))
        property.delete()
        return Response({'success': 'Successfully deleted the property'}, status=status.HTTP_200_OK)
    
class BookingViewset(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "put", "delete"]
    serializer_class = BookingSerializer
    queryset = Booking.objects.select_related('user', 'property_id').all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        property = serializer.validated_data.get('property_id')
        user = request.user
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        booking = Booking.objects.create(property_id=property.property_id,
                                        user=user, start_date=start_date,
                                        end_date=end_date, total_price=property.pricepernight)
        serializer = self.get_serializer(booking)
        email_verification.delay(name=booking.user.first_name, email=booking.user.email)
        return Response({'success': 'Successfully booked a property',
                        'data': serializer.data
                        }, status=status.HTTP_201_CREATED)
        
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        booking = get_object_or_404(Booking, booking_id=kwargs.get('pk'))
        serializer = self.get_serializer(data=request.data, instance=booking, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(booking)
        return Response({'success': 'Successfully updated a booking',
                        'data':serializer.data}, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        booking = get_object_or_404(Booking, booking_id=kwargs.get('pk'))
        booking.delete()
        return Response({'success': 'Successfully deleted the booking'}, status=status.HTTP_200_OK)

def generate_tx_ref(booking_id: str) -> str:
    # Take only first 12 chars of booking_id (or whatever you use)
    short_booking = str(booking_id)[:12]  
    
    # Add a short unique string (8 chars max)
    unique_suffix = uuid.uuid4().hex[:8]  

    tx_ref = f"{short_booking}-{unique_suffix}"

    # Ensure it does not exceed 50 chars
    return tx_ref[:50]

@csrf_exempt
def payment_view(request, *args, **kwargs):
    if request.method == "POST":
        booking = get_object_or_404(Booking, booking_id=kwargs.get('pk'))
        url = "https://api.chapa.co/v1/transaction/initialize"
        headers = {
            'Authorization': f'Bearer {os.getenv("CHAPA_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }
        payload = {
            "amount": float(5000 * 100),  # Convert to cents
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "phone_number": booking.user.phone_number,
            "tx_ref": generate_tx_ref(booking.booking_id),
            "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
            "return_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
            "customization": {
                "title": f"{booking.property_id.name}",
                "description": "I love online payments"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        print(data['status'])
        if data['status'] != 'success':
            return JsonResponse(data, status=response.status_code)
        Payment.objects.create(
            booking=booking,
            amount=payload['amount'] / 100,  # Convert back to original amount
            status='completed',
            transaction_id=payload['tx_ref']
        )
        # email_verification.delay(booking.user.email, booking.property_id.name)
        return JsonResponse(data, status=response.status_code)
