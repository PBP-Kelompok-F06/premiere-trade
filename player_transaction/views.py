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

@login_required(login_url='/login')
def menampilkan_list_pemain_yang_sedang_dijual(request):
    pemain_list = Player.objects.filter(sedang_dijual = True)

    context = {
        'pemain_list': pemain_list,
    }

    return render(request, "list_pemain_dijual.html", context)

@login_required(login_url='/login')
def list_pemain_saya(request):
    """Tampilkan pemain milik klub admin yang sedang login"""
    profile = get_object_or_404(Profile, user=request.user)
    pemain_list = Player.objects.filter(current_club=profile.managed_club)
    return render(request, "club_saya.html", {"pemain_list": pemain_list})


@login_required(login_url='/login')
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

@login_required(login_url='/login')
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

@login_required(login_url='/login')
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
@login_required(login_url='/login')
@user_passes_test(club_admin_required)
def negotiation_inbox(request):
    profile = get_object_or_404(Profile, user=request.user)
    club = profile.managed_club

    if not club:
        return render(request, 'error.html', {"message": "Anda belum memiliki klub untuk dikelola."})

    received_offers = Negotiation.objects.filter(to_club=club).order_by('-created_at')
    sent_offers = Negotiation.objects.filter(from_club=club).order_by('-created_at')

    return render(request, 'negotiation_inbox.html', {
        'received_offers': received_offers,
        'sent_offers': sent_offers,
        'club': club,
    })


# --- Kirim tawaran (dari halaman pemain dijual) ---
@login_required(login_url='/login')
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
@login_required(login_url='/login')
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
        player.current_club = nego.from_club  # 🔥 Pemain berpindah ke klub pembeli
        player.sedang_dijual = False
        player.save()

        # ✅ Batalkan semua negosiasi lain pada pemain ini
        Negotiation.objects.filter(player=player).exclude(id=nego.id).update(status='cancelled')

    elif action == 'reject':
        nego.status = 'rejected'
        nego.save()
        message = f"Tawaran dari {nego.from_club.name} ditolak."
    else:
        return JsonResponse({'success': False, 'message': 'Aksi tidak valid.'})

    nego.save()
    return JsonResponse({'success': True, 'message': f'Tawaran {action}ed!'})


























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