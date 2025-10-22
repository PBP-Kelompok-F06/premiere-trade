from django.db import models


# Create your models here.
class Club(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, blank=True)
    # Kita pakai URLField agar bisa menyimpan link ke logo dari Transfermarkt
    logo_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    # Relasi ke Club. related_name='players' sangat membantu
    # on_delete=models.CASCADE berarti jika Klub dihapus, pemainnya juga.
    current_club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="players"
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_pemain = models.CharField(max_length=255)
    position = models.CharField(max_length=50)
    umur = models.IntegerField()
    market_value = models.IntegerField()
    negara = models.CharField(max_length=255)
    jumlah_goal = models.IntegerField()
    jumlah_asis = models.IntegerField()
    jumlah_match = models.IntegerField()
    sedang_dijual = models.BooleanField()
    
    def __str__(self):
        return self.nama_pemain

    def __str__(self):
        return self.name
