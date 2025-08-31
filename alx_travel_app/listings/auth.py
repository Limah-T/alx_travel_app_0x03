from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(style={'input_type': 'password'}, 
                                    write_only=True)    

    class Meta:
        model = User
        fields = [
            'user_id', 'first_name', 'last_name',
            'email', 'password'
            ]

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError({'error': 'This field may not be blank!'})
        if len(value) < 8:
            raise serializers.ValidationError({'error': 'Password must be greater than or equal to 8.'})
        password = make_password(value)
        return password
    
    def create(self, validated_data):
        return super().create(validated_data)
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError({'error': 'This field may not be blank!'})
        if not User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError({'error': 'Unable to log in with the provided credentials'})
        return value.strip()
    
    
