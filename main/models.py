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

    name = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    # max_digits = total angka, decimal_places = angka di belakang koma
    # Ini cocok untuk menyimpan market value (misal: 150.50 juta)
    market_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name
