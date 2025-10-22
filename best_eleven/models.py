from django.db import models
from django.conf import settings
from django.contrib.auth.models import User # Use default User for now

class Club(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # logo_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DEF', 'Defender'),
        ('MID', 'Midfielder'),
        ('FWD', 'Forward'),
    ]

    name = models.CharField(max_length=100)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="players", null=True)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    profile_image_url = models.URLField(blank=True, null=True, help_text="URL ke foto profil pemain")
    market_value = models.CharField(max_length=50, blank=True, null=True, help_text="Nilai pasar pemain")
    nationality = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.club.name if self.club else 'N/A'}) - {self.market_value or 'N/A'}"

class BestEleven(models.Model):
    FORMATION_CHOICES = [
        ('4-4-2', '4-4-2'),
        ('4-3-3', '4-3-3'),
        ('3-5-2', '3-5-2'),
        ('4-2-3-1', '4-2-3-1'),
    ]

    fan_account = models.ForeignKey(
            settings.AUTH_USER_MODEL, 
            on_delete=models.CASCADE,
            related_name="best_elevens"
        )

    name = models.CharField(max_length=100)
    layout = models.CharField(
        max_length=10,
        choices=FORMATION_CHOICES,
        default='4-3-3'
    )
    players = models.ManyToManyField(Player)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - by {self.fan_account.username}"