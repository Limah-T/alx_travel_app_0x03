from .serializers import PropertySerializer, BookingSerializer, HostSerializer, HostProfileSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.cache import cache

from .utils.helper_functions import check_if_is_admin, check_single_user_in_cache_db, check_if_user_is_a_host, check_if_property_in_cache_db, check_if_user_has_booked
from .models import Property, Booking, Payment
from .tasks import email_verification
from .utils.tokens import get_token
from .models import Property, Booking, Host
from .serializers import PaymentSerializer
import uuid, os

def generate_random_uuid():
    count = 0
    uu = uuid.uuid4
    return f"{uu}_{count+1}" 

class ModifyHostViewset(viewsets.ModelViewSet):
    serializer_class = HostSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        all_hosts = cache.get("hosts")
        if all_hosts is None or all_hosts == []:
            all_host_details = list(Host.objects.all())
            cache.set("hosts", all_host_details)
            all_hosts = all_host_details
        return all_hosts
    
    def list(self, request, *args, **kwargs):
        admin_exist = check_single_user_in_cache_db(request.user.user_id)
        if not admin_exist:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        checking = check_if_is_admin(admin_exist)
        if not checking:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)  
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        admin_exist = check_single_user_in_cache_db(request.user.user_id)
        if not admin_exist:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        checking = check_if_is_admin(admin_exist)
        if not checking:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        
        user_uuid = kwargs.get("uuid")
        if user_uuid is None:
            return Response({'error': 'User UUID is missing'}, status=status.HTTP_400_BAD_REQUEST)
        user = check_if_user_is_a_host(user_uuid)
        if not user:
            return Response({'error': 'Host account does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        admin_exist = check_single_user_in_cache_db(request.user.user_id)
        if not admin_exist:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        checking = check_if_is_admin(admin_exist)
        if not checking:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        
        user_uuid = kwargs.get("uuid")
        if user_uuid is None:
            return Response({'error': 'User UUID is missing'}, status=status.HTTP_400_BAD_REQUEST)
        user = check_if_user_is_a_host(user_uuid)
        if not user:
            return Response({'error': 'Host account does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, instance=user, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

class HostViewset(viewsets.ModelViewSet):
    serializer_class = HostProfileSerializer
       
    def get_object(self):
        user = check_if_user_is_a_host(self.request.user.user_id)
        if not user:
            return Response({'error': 'Host account does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        return user
    
    def create(self, request, *args, **kwargs):
        user = check_if_user_is_a_host(request.user.user_id)
        if user:
            return Response({"error": "Host profile already exists for this user."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        valid_data = serializer.save()
        bio = valid_data['bio']
        address = valid_data['address']
        identity = valid_data['identity']
        social_link = valid_data['social_link']
        profile_photo = valid_data.get('profile_photo', None)
        host = Host.objects.create(host=request.user.user_id, bio=bio,
                                address=address, identity=identity,
                                social_link=social_link, profile_photo=profile_photo)
        if user.role != 'admin':
            user.role = 'host'
            user.save(update_fields=['role'])
        cache.set(f"host_profile_{host.host}", host)
        serializer = self.serializer_class(host)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        user = check_if_user_is_a_host(request.user.user_id)
        if not user:
            return Response({"error": "Host profile does not exist for this user."}, status=status.HTTP_404_NOT_FOUND)
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        user = check_if_user_is_a_host(request.user.user_id)
        if not user:
            return Response({"error": "Host profile does not exist for this user."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data, instance=user, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

class PropertyViewset(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    lookup_field = "uuid"

    def get_queryset(self):
        properties = cache.get("properties")
        if properties is None or properties == []:
            all_properties = list(Property.objects.filter(verification='verified'))
            properties = all_properties
            cache.set("properties", all_properties)          
            properties = all_properties
        return properties

    def create(self, request, *args, **kwargs):
        host = check_if_user_is_a_host(request.user.user_id)
        if not host:
            return Response({"error": "Host not found or inactive, or not a host, fill the host form to upgrade your account."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "guest":
            return Response({"error": "You cannot perform this account with a guest account, fill the host form to upgrade your account."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name']
        description = serializer.validated_data['description']
        location = serializer.validated_data['location']
        pricepernight = serializer.validated_data['pricepernight']
        property = Property.objects.create(user=request.user, name=name, description=description, 
                                           location=location, pricepernight=pricepernight)
        cache.set(f"property_{property.property_id}", property)
        serializer = self.serializer_class(property)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({"error": "User not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({"error": "User not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
        property = check_if_property_in_cache_db(kwargs.get('uuid'))
        if not property:
            return Response({'error': 'Property does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(property)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        host = check_if_user_is_a_host(request.user.user_id)
        if not host:
            return Response({"error": "Host not found or inactive, or not a host, fill the host form to upgrade your account."}, status=status.HTTP_404_NOT_FOUND)
        property = check_if_property_in_cache_db(kwargs.get('uuid'))
        if not property:
            return Response({'error': 'Property does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        if host.host != property.user.user_id or request.user.role != 'admin':
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data, instance=property, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(property)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def destroy(self, request, *args, **kwargs):
        host = check_if_user_is_a_host(request.user.user_id)
        if not host:
            return Response({"error": "Host not found or inactive, or not a host, fill the host form to upgrade your account."}, status=status.HTTP_404_NOT_FOUND)
        property = check_if_property_in_cache_db(kwargs.get('uuid'))
        if not property:
            return Response({'error': 'Property does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.role != 'admin':
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        property.verification = 'rejected'
        property.status = 'unavailable'
        property.save(update_fields=['verification', 'status'])
        return Response({'success': 'Successfully deleted the property'}, status=status.HTTP_200_OK)
    
class BookingViewset(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
        
    def create(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        property = check_if_property_in_cache_db(kwargs.get('uuid'))
        if not property:
            return Response({'error': 'Property does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        if property.user.user_id == user.user_id:
            return Response({'error': 'You cannot book your own property.'}, status=status.HTTP_400_BAD_REQUEST)
        if property.status != 'available' or property.verification != 'verified':
            return Response({'error': 'Property is not available for booking.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        booking = Booking.objects.create(property=property, user=user, start_date=start_date,
                                        end_date=end_date, total_price=property.pricepernight)
        serializer = self.serializer_class(booking)
        # email_verification.delay_on_commit(name=booking.user.first_name, email=booking.user.email)
        return Response({'success': 'Go ahead to pay for the booking',
                        'data': serializer.data}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        booking = kwargs.get("uuid")
        if booking is None:
            return Response({'error': 'Booking does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        admin_user = check_if_is_admin(user)
        if not admin_user:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data, instance=booking, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer = self.serializer_class(booking)
        return Response({"message": "Please proceed to make payment."}, status=status.HTTP_200_OK)

class PaymentViewset(APIView):
    serializer_class = PaymentSerializer

    def post(self, request, *argss, **kwargs):
        user = check_single_user_in_cache_db(request.user.user_id)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        booking_id = kwargs.get("uuid")
        if booking_id is None:
            return Response({'error': 'Booking does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        booking = check_if_user_has_booked(user.user_id, booking_id)
        if not booking:
            return Response({"error": "Booking does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        # if booking.status == "verified":
        #     return Response({"error": "Payment has been made already"}, status=status.HTTP_400_BAD_REQUEST)
        Payment.objects.create(
            booking=booking, amount=booking.total_price, transaction_id=generate_random_uuid()
        )
        booking.status="verified"
        booking.save(update_fields=["status"])
        token = get_token(booking.user.user_id, booking.user.email)
        email_verification.delay(
            subject="Email Verification",
            email=booking.user.email,
            txt_template_name="listings/text_mails/payment_successful.txt",
            verification_url=f"{os.environ.get('APP_DOMAIN')}/verify?token={token}"
        )
        self.serializer_class(booking)
        return Response({"success": "Payment made successfully"}, status=status.HTTP_200_OK)

# def generate_tx_ref(booking_id: str) -> str:
#     # Take only first 12 chars of booking_id (or whatever you use)
#     short_booking = str(booking_id)[:12]  
    
#     # Add a short unique string (8 chars max)
#     unique_suffix = uuid.uuid4().hex[:8]  

#     tx_ref = f"{short_booking}-{unique_suffix}"

#     # Ensure it does not exceed 50 chars
#     return tx_ref[:50]

# @csrf_exempt
# def payment_view(request, *args, **kwargs):
#     if request.method == "POST":
#         booking = get_object_or_404(Booking, booking_id=kwargs.get('pk'))
#         url = "https://api.chapa.co/v1/transaction/initialize"
#         headers = {
#             'Authorization': f'Bearer {os.getenv("CHAPA_SECRET_KEY")}',
#             'Content-Type': 'application/json'
#         }
#         payload = {
#             "amount": float(5000 * 100),  # Convert to cents
#             "currency": "ETB",
#             "email": booking.user.email,
#             "first_name": booking.user.first_name,
#             "last_name": booking.user.last_name,
#             "phone_number": booking.user.phone_number,
#             "tx_ref": generate_tx_ref(booking.booking_id),
#             "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
#             "return_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
#             "customization": {
#                 "title": f"{booking.property_id.name}",
#                 "description": "I love online payments"
#             }
#         }
#         response = requests.post(url, headers=headers, json=payload)
#         data = response.json()
#         if data['status'] != 'success':
#             return JsonResponse(data, status=response.status_code)
#         Payment.objects.create(
#             booking=booking,
#             amount=payload['amount'] / 100,  # Convert back to original amount
#             status='completed',
#             transaction_id=payload['tx_ref']
#         )
#         # email_verification.delay(booking.user.email, booking.property_id.name)
#         return JsonResponse(data, status=response.status_code)
