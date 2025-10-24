# rumors/models.py
import uuid
from django.db import models
from main.models import Player, Club
from accounts.models import CustomUser

class Rumors(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('denied', 'Denied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    pemain = models.ForeignKey(Player, on_delete=models.CASCADE)
    club_asal = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='rumor_asal', null=True, blank=True)
    club_tujuan = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='rumor_tujuan', null=True, blank=True)
    title = models.CharField(max_length=255, editable=False, null=True, blank=True)
    content = models.TextField(blank=True)
    rumors_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # New

    def save(self, *args, **kwargs):
        # Generate title otomatis
        if self.club_asal and self.club_tujuan and self.pemain:
            self.title = f"{self.pemain.nama_pemain} transfer from {self.club_asal.name} to {self.club_tujuan.name}"
        super().save(*args, **kwargs)

    def increment_views(self):
        self.rumors_views += 1
        self.save()

    def __str__(self):
        return self.title or "Rumor Tanpa Judul"
