from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from main.models import Player, Club

class Transaction(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sales')
    buyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='purchases')
    price = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.player.nama_pemain} - {self.seller} ➜ {self.buyer}"
    
class Negotiation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'), 
    ]

    from_club = models.ForeignKey(Club, related_name='offers_sent', on_delete=models.CASCADE)
    to_club = models.ForeignKey(Club, related_name='offers_received', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    offered_price = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_club.name} → {self.to_club.name}: {self.player.nama_pemain} ({self.offered_price})"
