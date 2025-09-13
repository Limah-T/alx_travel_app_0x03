import attr
from rest_framework import serializers
from .models import Property, Booking, User, Host
from .auth_serializer import UserSerializer
from datetime import datetime

def check_date(value):
    now = datetime.now().date()
    time_input = datetime.strptime(str(value), '%Y-%m-%d').date()
    print(time_input)
    if time_input != now or time_input > now:
        return True
    return False

class PropertySerializer(serializers.Serializer):
    property_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(trim_whitespace=True)
    description = serializers.CharField(trim_whitespace=True)
    location = serializers.CharField(trim_whitespace=True)
    pricepernight = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return validated_data
    
    def update(self, instance, validated_data):
        name = validated_data.get('name', None)
        description = validated_data.get('description', None)
        location = validated_data.get('location', None)
        pricepernight = validated_data.get('pricepernight', None)
        validated_data.pop("verification", None)
        validated_data.pop("status", None)
        all_values = [name, description, location, pricepernight]
        if all(all_values) is None:
            raise serializers.ValidationError({'error': 'At least one field is required to update'})
        for attr, value in validated_data.items():
            if value is not None:
                setattr(instance, attr, value)
        instance.updated_at = datetime.today()
        instance.save()
        return instance

class HostSerializer(serializers.Serializer):
    host = serializers.UUIDField(read_only=True)
    bio = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)
    identity = serializers.CharField(read_only=True)
    social_link = serializers.CharField(read_only=True)
    profile_photo = serializers.CharField(read_only=True)
    verification_status = serializers.CharField(max_length=20, trim_whitespace=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def update(self, instance, validated_data):
        verified_status = validated_data.get("verification_status", None)
        if verified_status is not None:
            if verified_status not in ['verified', 'rejected', 'pending']:
                raise serializers.ValidationError({'verification_status': 'Invalid status. Choose from verified, rejected, pending.'})
            if verified_status == instance.verification_status:
                raise serializers.ValidationError({'verification_status': 'No change in verification status.'})
            instance.verification_status = verified_status
        instance.updated_at = datetime.today()
        instance.save(update_fields=['verification_status', 'updated_at'])
        return instance

class HostProfileSerializer(serializers.Serializer):
    host = serializers.UUIDField(read_only=True)
    bio = serializers.CharField(trim_whitespace=True)
    address = serializers.CharField(max_length=100, trim_whitespace=True)
    identity = serializers.CharField(max_length=50, trim_whitespace=True)
    social_link = serializers.CharField(max_length=255, trim_whitespace=True)
    profile_photo = serializers.CharField(max_length=255, trim_whitespace=True, required=False, allow_null=True, allow_blank=True)
    verification_status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    property = PropertySerializer(many=True, read_only=True)

    def create(self, validated_data):
        link = validated_data['social_link']
        try:
            Host.objects.get(social_link=link.strip())
            raise serializers.ValidationError({'social_link': 'link already exists'}) 
        except Host.DoesNotExist:
            return validated_data
        
    def update(self, instance, validated_data):
        bio = validated_data.get("bio")
        address = validated_data.get("address")
        identity = validated_data.get("identity")
        social_link = validated_data.get("social_link")
        profile_photo = validated_data.get("profile_photo")
        validated_data.pop("verification_status", None)
        if bio.strip() == instance.bio and address.strip() == instance.address and identity.strip() == instance.identity and social_link.strip() == instance.social_link and profile_photo.strip() == instance.profile_photo:
            raise serializers.ValidationError("Nothing to update.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value.strip())
        instance.updated_at = datetime.today()
        instance.save()
        return instance
    
class BookingSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField(read_only=True)
    user = serializers.UUIDField(read_only=True)
    property_id = serializers.UUIDField(read_only=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()   
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    # def validate_property_id(self, value):
    #     if not Property.objects.filter(property_id=value).exists():
    #         raise serializers.ValidationError({'error': 'Property does not exist!'})
    #     value_object = Property.objects.get(property_id=value)
    #     return value_object
    
    def validate_start_date(self, value):
        if not check_date(value):
            raise serializers.ValidationError({'error': 'You cannot book for a past date (start_date)'})
        return value
    
    def validate_end_date(self, value):
        if not check_date(value):
            raise serializers.ValidationError({'error': 'You cannot book for a past date (end_date)'})
        return value
    
    def create(self, validated_data):
        return validated_data
    
class PaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField(read_only=True)
    booking = BookingSerializer(read_only=True)
    amount = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField(read_only=True)

    def create(self, validated_data):
        return validated_data