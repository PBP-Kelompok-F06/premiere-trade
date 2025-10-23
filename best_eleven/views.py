from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
import json, traceback
from main.models import Player, Club 
from .models import BestEleven


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BestElevenBuilderView(LoginRequiredMixin, TemplateView):
    template_name = 'best_eleven/besteleven_builder.html'
    login_url = '/admin/login/'


@login_required
def get_builder_data(request):
    """ Ambil semua klub & formasi user """
    try:
        clubs = Club.objects.order_by('name')
        club_list = [{'id': c.id, 'name': c.name} for c in clubs]

        formations = BestEleven.objects.filter(fan_account=request.user).order_by('-updated_at')
        formation_history = [{'id': f.id, 'name': f.name, 'layout': f.layout} for f in formations]

        return JsonResponse({'clubs': club_list, 'history': formation_history})
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': 'Gagal memuat data awal.'}, status=500)


@login_required
def get_players_by_club_api(request):
    """ Ambil semua pemain (atau filter by club) """
    try:
        club_id = request.GET.get('club_id')
        players = Player.objects.filter(current_club_id=club_id) if club_id else Player.objects.all()

        player_list = [
            {
                'id': p.id,
                'name': p.nama_pemain,
                'club_name': p.current_club.name if p.current_club else 'N/A',
                'position': p.position,
                'nationality': p.negara or '-',
                'market_value': p.market_value or 0,
                'profile_image_url': p.thumbnail or '',
            }
            for p in players
        ]
        return JsonResponse({'players': player_list})
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': 'Gagal memuat daftar pemain.'}, status=500)


@login_required
def save_formation_api(request):
    """ Simpan atau update formasi """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required.'}, status=405)

    try:
        data = json.loads(request.body)
        name = data.get('name')
        layout = data.get('layout')
        player_ids_data = data.get('player_ids')
        formation_id = data.get('formation_id')

        if not all([name, layout, player_ids_data]) or len(player_ids_data) != 11:
            return JsonResponse({'error': 'Nama, layout, dan 11 pemain wajib diisi.'}, status=400)

        player_ids = [p['playerId'] for p in player_ids_data]
        user = request.user

        if formation_id:
            formation = get_object_or_404(BestEleven, pk=formation_id, fan_account=user)
            formation.name = name
            formation.layout = layout
        else:
            formation = BestEleven.objects.create(fan_account=user, name=name, layout=layout)

        formation.players.set(player_ids)
        formation.save()

        return JsonResponse({
            'success': True,
            'formation': {'id': formation.id, 'name': formation.name, 'layout': formation.layout},
            'message': 'Formasi berhasil disimpan!'
        })
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'Gagal menyimpan formasi.'}, status=500)


@login_required
def get_formation_details_api(request, pk):
    """ Ambil detail formasi tertentu """
    try:
        formation = get_object_or_404(
            BestEleven.objects.prefetch_related('players__current_club'),
            pk=pk,
            fan_account=request.user
        )

        players_data = [
            {
                'id': p.id,
                'name': p.nama_pemain,
                'position': p.position,
                'market_value': p.market_value or 0,
                'nationality': p.negara or '-',
                'profile_image_url': p.thumbnail or '',
                'club_name': p.current_club.name if p.current_club else 'N/A',
            }
            for p in formation.players.all()
        ]

        return JsonResponse({
            'id': formation.id,
            'name': formation.name,
            'layout': formation.layout,
            'players': players_data
        })
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': 'Gagal mengambil detail formasi.'}, status=500)
