# main/views.py

from django.shortcuts import render, get_object_or_404
from .models import Club, Player # Pastikan model Club & Player ada di sini

def homepage(request):
    """
    Menampilkan halaman utama dengan 4 klub unggulan 
    dan 4 pemain termahal dari masing-masing klub.
    """
    featured_club_names = ["Chelsea", "Arsenal", "Manchester City", "Liverpool"]
    featured_clubs_data = []

    for club_name in featured_club_names:
        try:
            # Ambil objek klub berdasarkan nama
            club = Club.objects.get(name=club_name)
            # Ambil 4 pemain termahal dari klub ini, urutkan descending
            top_players = club.players.all().order_by('-market_value')[:4]
            featured_clubs_data.append({
                'club': club,
                'top_players': top_players
            })
        except Club.DoesNotExist:
            # Handle jika klub tidak ditemukan (opsional)
            print(f"Peringatan: Klub '{club_name}' tidak ditemukan di database.")
            featured_clubs_data.append({
                'club': {'name': club_name, 'id': None}, # Sediakan nama & id dummy
                'top_players': []
            })
        except Exception as e:
             # Handle error lain jika perlu
            print(f"Error saat mengambil data untuk {club_name}: {e}")
            featured_clubs_data.append({
                'club': {'name': club_name, 'id': None},
                'top_players': []
            })


    context = {
        'user': request.user,
        'featured_clubs_data': featured_clubs_data, # Kirim data klub & pemain
    }
    return render(request, 'main/homepage.html', context)

# --- VIEW BARU UNTUK DAFTAR SEMUA PEMAIN PER KLUB ---
def player_list_by_club(request, club_id):
    """
    Menampilkan daftar semua pemain dari klub tertentu.
    """
    club = get_object_or_404(Club, id=club_id)
    players = club.players.all().order_by('nama_pemain') # Urutkan berdasarkan nama

    context = {
        'club': club,
        'players': players,
    }   
    # Kita akan bikin template baru 'player_list.html'
    return render(request, 'main/player_list.html', context)