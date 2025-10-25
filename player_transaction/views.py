import datetime, json
from main.models import Player
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from django.core import serializers
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from accounts.models import Profile, CustomUser
from main.models import Player, Club
from player_transaction.models import Negotiation

def club_admin_required(user):
    return user.is_authenticated and user.is_club_admin

@login_required(login_url='/accounts/login/')
def list_pemain_dijual_view(request):
    """Menampilkan halaman list pemain yang sedang dijual (HTML)"""
    return render(request, "list_pemain_dijual.html")

@login_required(login_url='/accounts/login/')
def list_pemain_dijual_json(request):
    """Endpoint AJAX: Mengembalikan daftar pemain yang sedang dijual (JSON)"""
    pemain_list = Player.objects.filter(sedang_dijual=True).select_related('current_club')
    data = [
        {
            "id": p.id,
            "nama_pemain": p.nama_pemain,
            "posisi": p.position,
            "umur": p.umur,
            "negara": p.negara,
            "match": p.jumlah_match,
            "goal": p.jumlah_goal,
            "assist": p.jumlah_asis,
            "market_value": p.market_value,
            "thumbnail": p.thumbnail,
            "nama_klub": p.current_club.name if p.current_club else "-",
        }
        for p in pemain_list
    ]

    return JsonResponse(data, safe=False)

@login_required(login_url='/accounts/login/')
def list_pemain_saya(request):
    """Endpoint AJAX: mengembalikan daftar pemain milik klub user login (format JSON)."""
    profile = get_object_or_404(Profile, user=request.user)
    klub = profile.managed_club

    # Ambil semua pemain klub yang dikelola user login
    pemain_list = Player.objects.filter(current_club=klub).select_related('current_club')

    data = [
        {
            "id": p.id,
            "nama_pemain": p.nama_pemain,
            "posisi": p.position,
            "umur": p.umur,
            "negara": p.negara,
            "match": p.jumlah_match,
            "goal": p.jumlah_goal,
            "assist": p.jumlah_asis,
            "market_value": p.market_value,
            "sedang_dijual": p.sedang_dijual,
            "thumbnail": p.thumbnail,
        }
        for p in pemain_list
    ]

    return JsonResponse(data, safe=False)

@login_required(login_url='/accounts/login/')
def club_saya_view(request):
    """Menampilkan halaman My Club (HTML)"""
    return render(request, "club_saya.html")


@login_required(login_url='/accounts/login/')
@require_POST
def jual_pemain_ajax(request, player_id):
    """Ubah status pemain jadi sedang dijual (AJAX)"""
    profile = get_object_or_404(Profile, user=request.user)
    player = get_object_or_404(Player, id=player_id, current_club=profile.managed_club)

    player.sedang_dijual = True
    player.save()

    return JsonResponse({
        'success': True,
        'message': f'{player.nama_pemain} sekarang masuk ke Transfer Market!',
        'player_id': str(player.id),
        'nama': player.nama_pemain,
    })

@login_required(login_url='/accounts/login/')
@require_POST
def batalkan_jual_pemain_ajax(request, player_id):
    """Batalkan penjualan pemain milik klub sendiri"""
    profile = get_object_or_404(Profile, user=request.user)
    player = get_object_or_404(Player, id=player_id, current_club=profile.managed_club)

    if not player.sedang_dijual:
        return JsonResponse({'success': False, 'message': 'Pemain ini tidak sedang dijual.'})

    player.sedang_dijual = False
    player.save()

    return JsonResponse({
        'success': True,
        'message': f"Penjualan {player.nama_pemain} telah dibatalkan."
    })

@login_required(login_url='/accounts/login/')
@require_POST
def beli_pemain_ajax(request, player_id):
    """Admin club membeli pemain dari transfer market"""
    profile = get_object_or_404(Profile, user=request.user)
    pembeli_club = profile.managed_club
    player = get_object_or_404(Player, id=player_id)

    if player.current_club == pembeli_club:
        return JsonResponse({'success': False, 'message': 'Tidak bisa membeli pemain klub sendiri.'})

    player.current_club = pembeli_club
    player.sedang_dijual = False
    player.save()

    Negotiation.objects.filter(player=player, status='pending').update(status='cancelled')

    return JsonResponse({
        'success': True,
        'message': f"{player.nama_pemain} berhasil dibeli oleh {pembeli_club.name}!"
    })

# --- Inbox (hanya untuk admin club) ---
@login_required(login_url='/accounts/login/')
@user_passes_test(club_admin_required)
def negotiation_inbox_view(request):
    """Render halaman inbox negosiasi (HTML kosong, isi via AJAX)"""
    profile = get_object_or_404(Profile, user=request.user)
    club = profile.managed_club

    if not club:
        return render(request, 'error.html', {"message": "Anda bukan admin klub."})

    return render(request, 'negotiation_inbox.html', {"club": club})


@login_required(login_url='/accounts/login/')
@user_passes_test(club_admin_required)
def negotiation_inbox_json(request):
    """Endpoint AJAX — mengembalikan data negosiasi dalam format JSON"""
    profile = get_object_or_404(Profile, user=request.user)
    club = profile.managed_club

    if not club:
        return JsonResponse({"error": "Anda bukan admin klub."}, status=400)

    received_offers = Negotiation.objects.filter(to_club=club).select_related('from_club', 'player').order_by('-created_at')
    sent_offers = Negotiation.objects.filter(from_club=club).select_related('to_club', 'player').order_by('-created_at')

    data = {
        "received_offers": [
            {
                "id": n.id,
                "from_club": n.from_club.name,
                "player": n.player.nama_pemain,
                "offered_price": float(n.offered_price),
                "status": n.get_status_display(),  # biar tampil "Accepted" bukan "accepted"
                "created_at": n.created_at.strftime("%d %B %Y, %H:%M"),
            }
            for n in received_offers
        ],
        "sent_offers": [
            {
                "id": n.id,
                "to_club": n.to_club.name,
                "player": n.player.nama_pemain,
                "offered_price": float(n.offered_price),
                "status": n.get_status_display(),
                "created_at": n.created_at.strftime("%d %B %Y, %H:%M"),
            }
            for n in sent_offers
        ]
    }

    return JsonResponse(data)



# --- Kirim tawaran (dari halaman pemain dijual) ---
@login_required(login_url='/accounts/login/')
@user_passes_test(club_admin_required)
@require_POST
def send_negotiation(request, player_id):
    try:
        data = json.loads(request.body)
        offered_price = data.get('offered_price')

        profile = get_object_or_404(Profile, user=request.user)
        from_club = profile.managed_club

        player = get_object_or_404(Player, id=player_id)
        to_club = player.current_club

        if from_club == to_club:
            return JsonResponse({'success': False, 'message': 'Tidak bisa menawar pemain dari klub sendiri.'})

        Negotiation.objects.create(
            from_club=from_club,
            to_club=to_club,
            player=player,
            offered_price=offered_price,
        )

        return JsonResponse({'success': True, 'message': 'Tawaran berhasil dikirim!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# --- Aksi accept/reject ---
@login_required(login_url='/accounts/login/')
@user_passes_test(club_admin_required)
@require_POST
def respond_negotiation(request, nego_id, action):
    nego = get_object_or_404(Negotiation, id=nego_id)
    profile = get_object_or_404(Profile, user=request.user)
    club = profile.managed_club

    # Pastikan klub yang login adalah penerima tawaran
    if nego.to_club != club:
        return JsonResponse({'success': False, 'message': 'Anda tidak berhak merespons tawaran ini.'})

    if action == 'accept':
        nego.status = 'accepted'
        nego.save()

        player = nego.player
        player.current_club = nego.from_club  #  Pemain berpindah ke klub pembeli
        player.sedang_dijual = False
        player.save()

        #  Batalkan semua negosiasi lain pada pemain ini
        Negotiation.objects.filter(player=player).exclude(id=nego.id).filter(status='pending').update(status='cancelled')
        new_status = "Accepted"

    elif action == 'reject':
        nego.status = 'rejected'
        nego.save()
        message = f"Tawaran dari {nego.from_club.name} ditolak."
        new_status = "Rejected"
    else:
        return JsonResponse({'success': False, 'message': 'Aksi tidak valid.'})

    nego.save()
    return JsonResponse({'success': True, 'message': f'Tawaran {action}ed!', 'new_status': new_status})


























def show_xml(request):
     pemain_list = Player.objects.all()
     xml_data = serializers.serialize("xml", pemain_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    pemain_list = Player.objects.select_related('current_club').all()
    
    data = [
        {
            'id': str(pemain.id),
            'nama_pemain': pemain.nama_pemain,
            'club': pemain.current_club.name,
            'umur': pemain.umur,
            'market_value': pemain.market_value,
            'negara': pemain.negara,
            'jumlah_goal': pemain.jumlah_goal,
            'jumlah_asis': pemain.jumlah_asis,
            'jumlah_match': pemain.jumlah_match,
            'sedang_dijual': pemain.sedang_dijual,
        }
        for pemain in pemain_list
    ]

    return JsonResponse(data, safe=False, json_dumps_params={'indent': 2})


def show_xml_by_id(request, product_id):
   try:
       product_item = Player.objects.filter(pk=product_id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Player.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, product_id):
    try:
        pemain = Player.objects.select_related('current_club').get(pk=product_id)
        data = {
            'id': str(pemain.id),
            'nama_pemain': pemain.nama_pemain,
            'club': pemain.current_club.name,
            'umur': pemain.umur,
            'market_value': pemain.market_value,
            'negara': pemain.negara,
            'jumlah_goal': pemain.jumlah_goal,
            'jumlah_asis': pemain.jumlah_asis,
            'jumlah_match': pemain.jumlah_match,
            'sedang_dijual': pemain.sedang_dijual,
        }
        return JsonResponse(data)
    except Player.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)