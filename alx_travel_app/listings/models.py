from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
import uuid

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, phone_number, password=None, **extra_fields):
        if not all([first_name, last_name, email, phone_number]):
            raise ValueError('All fields must be set')
        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(first_name, last_name, email, phone_number, password, **extra_fields)

class User(AbstractUser):
    username=None
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    pending_email = models.EmailField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=[
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin')
    ], default='guest')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    reset_password = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    def save(self, *args, **kwargs):
        if self.first_name:
            self.first_name = self.first_name.strip().title()
        if self.last_name:
            self.last_name = self.last_name.strip().title()
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def confirm_pending_email(self):
        """Confirming pending email after verification"""
        if self.pending_email:
            self.email = self.pending_email.strip().lower()
            self.pending_email = None
            self.save(update_fields=["email", "pending_email"])
    
class Property(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')  #
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    location = models.CharField(max_length=255, null=False, blank=False)
    pricepernight = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().title()
        if self.location:
            self.location = self.location.strip().title()
        super().save(*args, **kwargs)

class Booking(models.Model):
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')  
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')  
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')  
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')  
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=0)
    comment = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')  
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], default='pending')
    transaction_id = models.CharField(max_length=255, unique=True)
