from rest_framework import serializers
from .models import Property, Booking, User, Host
from .auth_serializer import UserSerializer
from datetime import datetime

def check_date(value):
    now = datetime.now().date()
    if value < now:
        return False
    return True

class HostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Host
        fields = '__all__'

    def create(self, validated_data):
        link = validated_data.get('social_link')
        if link is not None:
            try:
                Host.objects.get(social_link=link.strip())
            except Host.DoesNotExist:
                raise serializers.ValidationError({'social_link': 'link already exists'})    
        return validated_data

    def update(self, instance, validated_data):
        bio = validated_data.get("bio")
        address = validated_data.get("address")
        identity = validated_data.get("identity")
        social_link = validated_data.get("social_link")
        profile_photo = validated_data.get("profile_photo")
        if bio.strip() == instance.bio and address.strip() == instance.address and identity.strip() == instance.id and social_link.strip() == instance.social_link and profile_photo.strip() == instance.profile_photo:
            raise serializers.ValidationError("Nothing to update.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value.strip())
        instance.updated_at = datetime.today()
        instance.save()
        return instance
     
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
        name = validated_data['name']
        description = validated_data['description']
        location = validated_data['location']
        pricepernight = validated_data['pricepernight']
        if name.title()==instance.name and description==instance.description and location.title()==instance.location and pricepernight==instance.pricepernight:
            raise serializers.ValidationError({'Nothing to update'})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_at = datetime.today()
        instance.save
        return instance
    
class BookingSerializer(serializers.ModelSerializer):
    property_id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    # For output
    booking_id = serializers.UUIDField(read_only=True)
    user = serializers.UUIDField(read_only=True)
    property_id = serializers.UUIDField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)

    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def validate_property_id(self, value):
        if not Property.objects.filter(property_id=value).exists():
            raise serializers.ValidationError({'error': 'Property does not exist!'})
        value_object = Property.objects.get(property_id=value)
        return value_object
    
    def validate_start_date(self, value):
        if not check_date(value):
            raise serializers.ValidationError({'error': 'You cannot book for a past date (start_date)'})
        return value
    
    def validate_end_date(self, value):
        if not check_date(value):
            raise serializers.ValidationError({'error': 'You cannot book for a past date (end_date)'})
        return value
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
