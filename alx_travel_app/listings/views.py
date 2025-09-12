from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import authentication_classes, permission_classes, api_view, renderer_classes

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .utils.helper_functions import check_if_is_admin, check_single_user_in_cache_db
from .serializers import PropertySerializer, BookingSerializer
from .auth_serializer import UserSerializer, LoginSerializer, ResetPasswordSerializer, SetPasswordSerializer, ChangePasswordSerializer
from .models import Property, Booking, User, Payment
from .tasks import email_verification
from .utils.tokens import get_token, decode_token
from dotenv import load_dotenv
import os, requests, uuid

load_dotenv(override=True)

class UserApiView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ["post"]
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_token(user_id=user.user_id, email=user.email)
        print(f"{os.environ.get('APP_DOMAIN')}/verify?token={token}")
        email_verification.delay_on_commit(
            subject="Email Verification",
            email=user.email,
            txt_template_name="listings/text_mails/signup.txt",
            verification_url=f"{os.environ.get('APP_DOMAIN')}/verify?token={token}"
        )
        return Response({"message": "please check your email for verification."}, status=status.HTTP_200_OK)

@extend_schema(methods=["GET"], request=None,
    parameters=[
        OpenApiParameter("token", str, OpenApiParameter.QUERY, True, description="Deactivation token")
    ],
    responses={
        200: OpenApiResponse(description="Account deactivated successfully"),
        400: OpenApiResponse(description="Invalid or expired token / bad credentials"),
    }
)
@api_view(["get"])
@authentication_classes([])
@permission_classes([])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def Verify_signup_token(request):
    token = request.GET.get("token") or request.query_params.get("token")
    if not token:
        return Response({"error": "Token is missing"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    payload = decode_token(token)
    if not payload:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    email = payload.get("sub")
    uuid = payload.get("iss")
    if not email:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    try:
        user = User.objects.get(email=email, user_id=uuid)
    except User.DoesNotExist:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    if not user.is_active:
        return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    user.verified=True
    user.save(update_fields=["verified"])
    cache.set(f"user_profile_{user.user_id}", user)
    return Response({"success": "Email has been verified successfully"}, status=status.HTTP_200_OK, template_name="listings/valid_email.html")

class LoginApiView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ["post"]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'error': 'Unable to log in with the provided credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.verified:
            return Response({"error": "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        cache.set(f"user_profile_{user.user_id}", user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    
class ModifyUserViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        users = cache.get("users")
        if users is None:
            all_users = list(User.objects.values("user_id", "first_name", "last_name", "email", "phone_number"))
            cache.set("users", all_users)
            users = all_users
        return users

    def list(self, request, *args, **kwargs):
        admin_exist = check_single_user_in_cache_db(request.user.user_id)
        if not admin_exist:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        checking = check_if_is_admin(admin_exist)
        if not checking:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        user = check_single_user_in_cache_db(user_uuid)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        admin_exist = check_single_user_in_cache_db(request.user.user_id)
        if not admin_exist:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        checking = check_if_is_admin(admin_exist)
        if not checking:
            return Response({'error': 'You do not have permission to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        user_uuid = kwargs.get("uuid")
        if user_uuid is None:
            return Response({'error': 'User UUID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        user = check_single_user_in_cache_db(user_uuid)
        if not user:
            return Response({'error': 'User does not exist or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = False
        user.save(update_fields=["is_active"])
        Token.objects.filter(user=user).delete()
        email_verification.delay(subject="Account Deactivation", email=user.email,
            txt_template_name="listings/text_mails/deactivate.txt",verification_url=f"{user.first_name} {user.last_name}")
        return Response({'message': f"{user.first_name} {user.last_name}'s account has been deactivated successfully by {admin_exist.first_name}"},
            status=status.HTTP_200_OK)

class UserProfileViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_active:
            return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.verified:
            return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if get_user is None:
            cache.set(user_profile, request.user)
            get_user = request.user
        serializer = self.serializer_class(get_user)
        return Response(serializer.data, status=status.HTTP_200_OK) 
  
    def update(self, request, *args, **kwargs):
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if not get_user:
            cache.set(f"user_profile_{request.user.user_id}", request.user)
            get_user = request.user
        if not get_user.is_active:
            return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        if not get_user.verified:
            return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.serializer_class(instance=get_user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.pending_email is not None:
            token = get_token(user_id=user.user_id, email=user.pending_email)
            email_verification.delay(subject="Update Email account", email=user.pending_email,
                               txt_template_name="listings/text_mails/update_email.txt", 
                               verification_url=f"{os.environ.get('APP_DOMAIN')}/verify_update?token={token}")
            return Response({"message": "Please check your email for verification"}, status=status.HTTP_200_OK)
        return Response({"success": "Profile has been updated successfully"}, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if not get_user:
            cache.set(f"user_profile_{request.user.user_id}", request.user)
            get_user = request.user
        if not get_user.is_active:
            return Response({"error": "User's account has been deactivated before now!"}, status=status.HTTP_400_BAD_REQUEST)
        token = get_token(user_id=get_user.user_id, email=get_user.email)
        email_verification(subject="Deactivate account?", email=get_user.email,
                               txt_template_name="listings/text_mails/deactivate_confirmation.txt", 
                               verification_url=f"{os.environ.get('APP_DOMAIN')}/deactivate_acct_verify?token={token}")
        return Response({"message": "Please check your email for verification"}, status=status.HTTP_200_OK)

@extend_schema(methods=["GET"], request=None,
    parameters=[
        OpenApiParameter("token", str, OpenApiParameter.QUERY, True, description="Deactivation token")
    ],
    responses={
        200: OpenApiResponse(description="Account deactivated successfully"),
        400: OpenApiResponse(description="Invalid or expired token / bad credentials"),
    })
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])    
def VerifyEmailUpdate(request):
    token = request.GET.get("token") or request.query_params.get("token")
    if not token:
        return Response({"error": "Token is missing"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    payload = decode_token(token)
    if not payload:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    email = payload.get("sub")
    uuid = payload.get("iss")
    if not email:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    try:
        user = User.objects.get(pending_email=email, user_id=uuid)
    except User.DoesNotExist:
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    user.confirm_pending_email()
    return Response({"success": "Email has been verified successfully"}, status=status.HTTP_200_OK, template_name="listings/valid_email.html")

@extend_schema(methods=["GET"], request=None,
    parameters=[
        OpenApiParameter("token", str, OpenApiParameter.QUERY, True, description="Deactivation token")
    ],
    responses={
        200: OpenApiResponse(description="Account deactivated successfully"),
        400: OpenApiResponse(description="Invalid or expired token / bad credentials"),
    }
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def VerifyAcctDeactivation(request):
    token = request.GET.get("token") or request.query_params.get("token")
    if not token:
        return Response({"error": "Token is missing"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    payload = decode_token(token)
    if not payload:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    email = payload.get("sub")
    uuid = payload.get("iss")
    if not email:
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    if not uuid:
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    try:
        user = User.objects.get(email=email, user_id=uuid)
    except User.DoesNotExist:
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    if not user.is_active:
        return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    user.verified=False
    user.is_active=False
    user.save(update_fields=["verified", "is_active"])
    Token.objects.filter(user=user).delete()
    return Response({"success": "Account has been deactivated successfully"}, status=status.HTTP_200_OK, template_name="listings/acct_deactivated.html")    

class ResetPassword(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = ResetPasswordSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["email"]
        if not user.is_active:
            return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.verified:
            return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        token = get_token(user_id=user.user_id, email=user.email)
        email_verification(
            subject="Reset Password", email=user.email, txt_template_name="listings/text_mails/reset_password_confirm.txt", verification_url=f"{os.environ.get('APP_DOMAIN')}/reset_password_verify?token={token}"
        )
        return Response({"message": "Please check your message for verification."}, status=status.HTTP_200_OK)

@extend_schema(methods=["GET"], request=None,
    parameters=[
        OpenApiParameter("token", str, OpenApiParameter.QUERY, True, description="Deactivation token")
    ],
    responses={
        200: OpenApiResponse(description="Account deactivated successfully"),
        400: OpenApiResponse(description="Invalid or expired token / bad credentials"),
    })
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def VerifyPasswordReset(request):
    token = request.GET.get("token") or request.query_params.get("token")
    if not token:
        return Response({"error": "Token is missing"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    payload = decode_token(token)
    if not payload:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    email = payload.get("sub")
    uuid = payload.get("iss")
    if not email:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    try:
        user = User.objects.get(email=email, user_id=uuid)
    except User.DoesNotExist:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    if not user.is_active:
        return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST, template_name="listings/invalid_email.html")
    if not user.verified:
        return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
    user.reset_password=True
    user.save(update_fields=["reset_password"])
    return Response({"message": "Please proceed to reset your password"}, status=status.HTTP_200_OK, template_name="listings/acct_deactivated.html") 

class SetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = SetPasswordSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user_data"]["user"]
        new_password = serializer.validated_data["user_data"]["new_password"]
        if not user.is_active:
            return Response({"error": "User's account has been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.verified:
            return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.reset_password:
            return Response({'error':'Please request for email to verify password reset'}, status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(new_password)
        user.reset_password = False
        user.save(update_fields=["password", "reset_password"])
        Token.objects.filter(user=user).delete()
        return Response({'success': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
    
class Change_passwordView(APIView):
    serializer_class = ChangePasswordSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if not get_user:
            cache.set(f"user_profile_{request.user.user_id}", request.user)
            get_user = request.user
        if not get_user.is_active:
            return Response({'error': "User's account as been deactivated"}, status=status.HTTP_400_BAD_REQUEST)
        if not get_user.verified:
            return Response({'error': "User's account has not been verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        if old_password.strip() == new_password.strip():
            return Response({"error": "Old and New password cannot be the-same."})
        if not check_password(old_password.strip(), request.user.password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.password = make_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"success": "Password has ben changed successfully"}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    http_method_names = ["post"]
    serializer_class = None  # avoids guessing for swaggerAPI

    def post(self, request, *args, **kwargs):
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if not get_user:
            cache.set(f"user_profile_{request.user.user_id}", request.user)
            get_user = request.user
        Token.objects.get(user=get_user).delete()
        return Response({"success": "Logout successfully"}, status=status.HTTP_200_OK)
    
class PropertyViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "put", "delete"]
    serializer_class = PropertySerializer
    # queryset = Property.objects.select_related('user').all()
    def get_queryset(self):
        properties = cache.get("properties")
        if not properties:
            all_properties = list(Property.objects.values('property_id', 'name', 'description', 'location', 'pricepernight'))
            cache.set(properties)
        return 

    def create(self, request, *args, **kwargs):
        user_profile = f"user_profile_{request.user.user_id}"
        get_user = cache.get(user_profile)
        if get_user is None:
            cache.set(user_profile, request.user)
            get_user = request.user
        if get_user.role == "guest":
            return Response({"error": "You cannot perform this account with a guest acccount, fill the host form"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name']
        description = serializer.validated_data['description']
        location = serializer.validated_data['location']
        pricepernight = serializer.validated_data['pricepernight']
        property = Property.objects.create(
                                user=get_user, name=name,
                                description=description, 
                                location=location, pricepernight=pricepernight)
        serializer = self.serializer_class(property)
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
        send_email.delay(name=booking.user.first_name, email=booking.user.email)
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
        # send_email.delay(booking.user.email, booking.property_id.name)
        return JsonResponse(data, status=response.status_code)
