from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, Host, Property
from django.core.cache import cache

def update_cache(instance, instance_key, key, queryset):
    """Utility to refresh cache for a model"""
    cache.delete(instance_key)
    cache.delete(key)
    cache.set(instance_key, instance)
    cache.set(key, list(queryset))

def delete_cache(instance_key, key, queryset):
    """Utility to delete cache for a model"""
    cache.delete(instance_key)
    cache.delete(key)
    cache.set(key, list(queryset))
    
@receiver(post_save, sender=User)
def update_user_cache(sender, instance, **kwargs):
    """Update user cache on save"""
    if instance.is_active:
        update_cache(
        instance=instance,
        instance_key=f"user_profile_{instance.user_id}",
        key="users",
        queryset=User.objects.filter(is_active=True, verified=True)
        )
        print(f"Cache updated for user_profile, and all users.")

@receiver(post_save, sender=Host)
def update_host_cache(sender, instance, **kwargs):
    """Update host cache on save"""
    update_cache(
        instance=instance,
        instance_key=f"host_profile_{instance.host}",
        key="hosts",
        queryset=Host.objects.all()
    )
    print(f"Cache updated for host_profile, and all hosts.")

@receiver(post_delete, sender=User)
def delete_user_cache(sender, instance, **kwargs):
    """Delete user cache on delete"""
    delete_cache(
        instance_key=f"user_profile_{instance.user_id}",
        key="users",
        queryset=User.objects.filter(is_active=True, verified=True)
    )
    print("Deleted cache for user_profile, and updated all users")

@receiver(post_delete, sender=Host)
def delete_host_cache(sender, instance, **kwargs):
    """Delete host cache on delete"""
    delete_cache(
        instance_key=f"host_profile_{instance.host}",
        key="hosts",
        queryset=Host.objects.all()
    )
    print("Deleted cache for host_profile, and updated all hosts")

@receiver(post_save, sender=Property)
def update_property_cache(sender, instance, **kwargs):
    """Update property cache on save"""
    update_cache(
        instance=instance,
        instance_key=f"property_{instance.property_id}",
        key="properties",
        queryset=Property.objects.filter(verification='verified')
    )
    print(f"Cache updated for property_{instance.property_id}, and all properties.")

@receiver(post_delete, sender=Property)
def delete_property_cache(sender, instance, **kwargs):
    """Delete property cache on delete"""
    delete_cache(
        instance_key=f"property_{instance.property_id}",
        key="properties",
        queryset=Property.objects.filter(status='verified')
    )
    print(f"Deleted cache for property_{instance.property_id}, and updated all properties.")