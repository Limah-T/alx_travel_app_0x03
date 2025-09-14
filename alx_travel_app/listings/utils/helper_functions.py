from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from listings.models import User, Host, Property, Booking

def check_if_is_admin(admin):
    if admin.verified and admin.is_superuser and admin.is_active:
        return True
    if not admin.verified:
        return False
    if not admin.is_active:
        return False

def check_single_user_in_cache_db(user_id):
    user = cache.get(f"user_profile_{user_id}")
    if user is None:
        try:
            instance = User.objects.get(user_id=user_id, verified=True, is_active=True)
            cache.set(f"user_profile_{user_id}", instance)
            user = instance
            return user
        except User.DoesNotExist:
            return False
    return user

def check_if_user_is_a_host(user_id):
    user = check_single_user_in_cache_db(user_id)
    if not user:
        return False
    try:
        host_cached = cache.get(f"host_profile_{user.user_id}")
        if host_cached is None:
            host = Host.objects.get(host=user.user_id)
            cache.set(f"host_profile_{user.user_id}", host)
            host_cached = host
    except Host.DoesNotExist:
        return False
    return host_cached

def check_if_property_in_cache_db(property_id):
    property = cache.get(f"property_{property_id}")
    if property is None:
        try:
            property_instance = Property.objects.get(property_id=property_id, status='verified')
            cache.set(f"property_{property_id}", property_instance)
            property = property_instance
            return property
        except Property.DoesNotExist:
            return False
    return property

def check_if_user_has_booked(user_id, booking_id):
    try:
        booking = Booking.objects.get(user__user_id=user_id, booking_id=booking_id)
    except Booking.DoesNotExist:
        return False
    return booking

# Get the Client Ip address
def get_client_ip(request):
    address = request.META.get('HTTP_X_FORWARDED_FOR')
    if address:
        ip_address = address.split(",")[0].strip()
    else:
        ip_address = request.META['REMOTE_ADDR']
    return ip_address
    