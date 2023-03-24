"""
Definition of models.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save 
from django.dispatch import receiver

class User(AbstractUser):
    linkedin_federation_id = models.CharField(max_length=500)
    google_federation_id = models.CharField(max_length=500)
    facebook_federation_id = models.CharField(max_length=500)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    picture = models.BinaryField()
    displayname = models.CharField(max_length=100)
    theme = models.CharField(max_length=20)
    address = models.TextField()

# receivers to add a Profile for newly created users
@receiver(post_save, sender=User) 
def create_user_profile(sender, instance, created, **kwargs):
     if created:
         Profile.objects.create(user=instance)
@receiver(post_save, sender=User) 
def save_user_profile(sender, instance, **kwargs):
     instance.profile.save()

