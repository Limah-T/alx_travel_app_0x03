from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from listings.models import User

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
            instance = User.objects.get(user_id=user_id)
            cache.set(f"user_profile_{user_id}", instance)
            user = instance
        except User.DoesNotExist:
            return False
    if not user.is_active:
        cache.delete(f"user_profile_{user.user_id}")
        return False
    return user