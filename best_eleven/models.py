from django.db import models
from django.conf import settings
from main.models import Club, Player



def __str__(self):
    return f"{self.nama_pemain} ({self.current_club.name if self.current_club else 'N/A'})"
    

class BestEleven(models.Model):
    FORMATION_CHOICES = [
        ('4-4-2', '4-4-2'),
        ('4-3-3', '4-3-3'),
        ('3-5-2', '3-5-2'),
        ('4-2-3-1', '4-2-3-1'),
    ]

    fan_account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="best_elevens")
    name = models.CharField(max_length=100)
    layout = models.CharField(max_length=10, choices=FORMATION_CHOICES, default='4-3-3')
    players = models.ManyToManyField(Player)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - by {self.fan_account.username}"
