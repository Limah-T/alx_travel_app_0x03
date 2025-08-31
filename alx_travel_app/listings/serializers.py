from rest_framework import serializers
from .models import Property, Booking, User
from datetime import datetime

def check_date(value):
    now = datetime.now().date()
    if value < now:
        return False
    return True

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

class PropertySerializer(serializers.ModelSerializer):
    property_id = serializers.UUIDField(read_only=True)
    user = serializers.UUIDField(read_only=True)
    bookings = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'
    
    def validate_user(self, value):
        return value.first_name
    
    def get_bookings(self, obj):
        return BookingSerializer(obj.bookings.all(), many=True).data
    
    def update(self, instance, validated_data):
        instance.updated_at = datetime.today()
        return super().update(instance, validated_data)