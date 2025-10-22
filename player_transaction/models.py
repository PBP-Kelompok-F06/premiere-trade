import uuid
from django.db import models
from accounts.models import CustomUser

class Pemain(models.Model):
    admin_club = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,related_name='pemain_dimiliki')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_pemain = models.CharField(max_length=255)
    club = models.CharField(max_length=255)
    umur = models.IntegerField()
    market_value = models.IntegerField()
    negara = models.CharField(max_length=255)
    jumlah_goal = models.IntegerField()
    jumlah_asis = models.IntegerField()
    jumlah_match = models.IntegerField()
    sedang_dijual = models.BooleanField()
    
    def __str__(self):
        return self.nama_pemain
    
