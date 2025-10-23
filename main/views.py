from django.shortcuts import render
from .models import Club, Player

# Create your views here.
def homepage(request):
    """
    Menampilkan halaman utama.
    Sekarang kita juga mengambil data semua klub.
    """
    # .prefetch_related('players') adalah cara efisien
    # untuk mengambil semua klub BESERTA pemain-pemainnya
    # tanpa membebani database.
    clubs = Club.objects.prefetch_related('players').all()
    
    context = {
        'user': request.user,
        'clubs': clubs, # Kirim data klub ke template
    }
    return render(request, 'homepage.html', context)

def show_players(request):
    players = Player.objects.all()  # ambil semua pemain dari database
    context = {
        'players': players
    }
    return render(request, 'players.html', context)
