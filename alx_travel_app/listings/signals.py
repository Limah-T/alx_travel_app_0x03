from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User
from django.core.cache import cache

@receiver(post_save, sender=User)
def update_user_cache(sender, instance, **kwargs):
    """Update user cache on save"""
    cache.delete(f"user_profile_{instance.user_id}")
    if not instance.is_active:
        pass
    else:
        cache.set(f"user_profile_{instance.user_id}", instance)
        all_users = list(User.objects.filter(is_active=True, verified=True))
        cache.set("users", all_users)
    print(f"Cache updated for user {instance.user_id}")

@receiver(post_delete, sender=User)
def delete_user_cache(sender, instance, **kwargs):
    """Delete user cache on delete"""
    print("here")
    cache.delete(f"user_profile_{instance.user_id}")
    print(f"Cache deleted for user {instance.user_id}")
    all_users = list(User.objects.filter(is_active=True, verified=True))
    cache.delete("users")
    cache.set("users", all_users)
    print("Cache updated for all users")