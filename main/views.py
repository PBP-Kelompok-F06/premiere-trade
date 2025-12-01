# main/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Club, Player

def homepage(request):
    """
    Menampilkan halaman utama dengan semua klub non-Admin 
    dan 4 pemain termahal dari masing-masing klub.
    """
    # Mengambil semua klub kecuali yang bernama 'Admin' (case-insensitive) dan diurutkan berdasarkan nama
    clubs = Club.objects.exclude(name__iexact='Admin').prefetch_related('players').order_by('name')
    featured_clubs_data = []

    for club in clubs:
        # Ambil 4 pemain termahal dari klub ini, urutkan descending
        top_players = club.players.all().order_by('-market_value')[:4]
        featured_clubs_data.append({
            'club': club,
            'top_players': top_players
        })

    context = {
        'user': request.user,
        'featured_clubs_data': featured_clubs_data,
    }
    return render(request, 'main/homepage.html', context)

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
    return render(request, 'main/player_list.html', context)

def show_clubs_json(request):
    """API untuk mengirim daftar klub sebagai JSON ke Flutter"""
    clubs = Club.objects.exclude(name__iexact='Admin').order_by('name')
    data = []
    for club in clubs:
        data.append({
            'pk': club.pk,
            'fields': {
                'name': club.name,
                'country': club.country,
                'logo_url': club.logo_url,
            }
        })
    return JsonResponse(data, safe=False)

def show_players_by_club_json(request, club_id):
    """API untuk mengirim daftar pemain per klub sebagai JSON ke Flutter"""
    # Pastikan ambil object Club atau 404 jika tidak ada, biar aman
    club = get_object_or_404(Club, pk=club_id)
    players = club.players.all().order_by('nama_pemain')
    
    data = []
    for player in players:
        data.append({
            'pk': str(player.id), # UUID convert ke string
            'fields': {
                'nama_pemain': player.nama_pemain,
                'position': player.position,
                'market_value': player.market_value,
                'thumbnail': player.thumbnail,
            }
        })
    return JsonResponse(data, safe=False)