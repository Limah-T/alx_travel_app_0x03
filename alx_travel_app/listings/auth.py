from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User

class UserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(trim_whitespace=True)
    last_name = serializers.CharField(trim_whitespace=True)
    email = serializers.EmailField(trim_whitespace=True)
    phone_number = serializers.CharField(trim_whitespace=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs.get("first_name") is None:
            raise serializers.ValidationError({'first_name': 'this field is required.'})
        if attrs.get("last_name") is None:
            raise serializers.ValidationError({'last_name': 'this field is required.'})
        if attrs.get("email") is None:
            raise serializers.ValidationError({'email': 'this field is required.'})
        if attrs.get("phone_number") is None:
            raise serializers.ValidationError({'phone_number': 'this field is required.'})
        if len(attrs.get("password")) < 8:
            raise serializers.ValidationError({'password': 'password must not be less than 8.'})
        return super().validate(attrs) 

    def create(self, validated_data):
        email = validated_data["email"]
        phone_number = validated_data["phone_number"]
        if User.objects.filter(email=email.lower()).exists():
            raise serializers.ValidationError({"email": "Email in use."})

        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "Phone number already exists."})
        user = User.objects.create_user(**validated_data)
        return user
    
    def update(self, instance, validated_data):
        email = validated_data["email"]
        phone_number = validated_data["phone_number"]
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        if email.lower() == instance.email and phone_number == instance.phone_number and first_name.title() == instance.first_name and last_name.title() == instance.last_name:
            raise serializers.ValidationError("Nothing to update.")
                  
        if instance.phone_number != phone_number:
            if User.objects.exclude(user_id=instance.user_id).filter(phone_number=phone_number).exists():
                raise serializers.ValidationError({"phone_number": "Phone number already exists."})
            instance.phone_number = phone_number
        if instance.email != email.lower():
            if User.objects.exclude(user_id=instance.user_id).filter(email=email.lower()).exists():
                raise serializers.ValidationError({"email": "Email in use."})
            instance.pending_email = email
        instance.first_name = first_name
        instance.last_name = last_name
        instance.save()
        return instance
        
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('This field may not be blank!')
        email = value.lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Unable to log in with the provided credentials')
        return email
           
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, trim_whitespace=True)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('This field may not be blank!')
        email = value.lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email provided.')
        return user 

class SetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, trim_whitespace=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", None)
        new_password = attrs.get("new_password", None)
        if email is None:
            raise serializers.ValidationError({'email':'This field may not be blank!'})
        if new_password is None:
            raise serializers.ValidationError({'new_password':'This field may not be blank!'})
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email provided.')
        user_data = {'user': user, 'new_password': new_password}
        self.context['user_data'] = user_data
        return self.context


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        old_password = attrs.get("old_password", None)
        new_password = attrs.get("new_password", None)
        if old_password is None:
            raise serializers.ValidationError({'old_password': 'This field may not be blank.'})
        if new_password is None:
            raise serializers.ValidationError({'new_password': 'This field may not be blank.'})
        if len(new_password.strip()) < 8:
            raise serializers.ValidationError({'new_password': 'Password length must be less than 8.'})
        return super().validate(attrs)