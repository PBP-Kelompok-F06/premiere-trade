from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    is_fan = models.BooleanField(default=True)
    is_club_admin = models.BooleanField(default=False)
    
    first_name = None
    last_name = None

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    managed_club = models.ForeignKey(
        'main.Club', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} Profile"
