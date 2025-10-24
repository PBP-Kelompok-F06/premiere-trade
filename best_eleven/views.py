from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.db import transaction
import json
import traceback
import uuid 

from main.models import Player, Club
from .models import BestEleven
from .forms import BestElevenForm


# --- Class-Based Views ---
@method_decorator(ensure_csrf_cookie, name='dispatch')
class BestElevenBuilderView(LoginRequiredMixin, TemplateView):
    template_name = 'best_eleven/besteleven_builder.html'
    login_url = '/admin/login/'

class BestElevenListView(LoginRequiredMixin, ListView):
    model = BestEleven
    template_name = 'best_eleven/besteleven_list.html'
    context_object_name = 'besteleven_list'

    def get_queryset(self):
        return BestEleven.objects.filter(fan_account=self.request.user).order_by('-updated_at')

class BestElevenDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = BestEleven
    template_name = 'best_eleven/besteleven_detail.html'
    context_object_name = 'formasi'

    def test_func(self):
        formation = self.get_object()
        return self.request.user == formation.fan_account

class FormationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BestEleven
    template_name = 'best_eleven/besteleven_confirm_delete.html'
    context_object_name = 'object'
    success_url = reverse_lazy('best_eleven:besteleven-list')

    def test_func(self):
        formation = self.get_object()
        return self.request.user == formation.fan_account

class BestElevenUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BestEleven
    form_class = BestElevenForm
    template_name = 'best_eleven/besteleven_form.html'

    def get_success_url(self):
        return reverse_lazy('best_eleven:besteleven-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        formation = self.get_object()
        return self.request.user == formation.fan_account


# --- API Views ---

@login_required
def get_builder_data(request):
    """ Ambil semua klub & formasi user """
    # (TIDAK BERUBAH)
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
    # (TIDAK BERUBAH)
    try:
        club_id = request.GET.get('club_id')
        player_qs = Player.objects.prefetch_related('current_club')
        players = player_qs.filter(current_club_id=club_id) if club_id else player_qs.all()

        player_list = [
            {
                # Kirim ID sebagai string karena ini UUID
                'id': str(p.id),
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


# --- PERBARUI FUNGSI save_formation_api ---
@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_formation_api(request):
    """ Simpan atau update formasi (TERMASUK DATA SLOT dengan UUID) """
    try:
        data = json.loads(request.body)
        name = data.get('name')
        layout = data.get('layout')
        player_ids_data = data.get('player_ids') # list of dicts: [{'slotId': 'GK', 'playerId': 'uuid-string'}, ...]
        formation_id = data.get('formation_id')

        if not all([name, layout, player_ids_data]) or len(player_ids_data) != 11:
            return JsonResponse({'error': 'Nama, layout, dan 11 pemain wajib diisi.'}, status=400)

        # Ekstrak Player IDs (sebagai string UUID) untuk M2M dan JSON
        # Pastikan tidak ada ID kosong atau None
        valid_player_ids_data = []
        player_ids_for_m2m = []
        for item in player_ids_data:
            player_id_str = item.get('playerId')
            if player_id_str: # Pastikan ID tidak kosong
                 valid_player_ids_data.append(item)
                 player_ids_for_m2m.append(player_id_str)
            else:
                 print(f"Warning: Received empty playerId in slot data: {item}")
                 # Anda bisa melempar error di sini jika ID kosong tidak diizinkan
                 # return JsonResponse({'error': 'playerId tidak boleh kosong.'}, status=400)

        # Validasi ulang jumlah setelah membersihkan ID kosong
        if len(valid_player_ids_data) != 11:
             return JsonResponse({'error': 'Harus ada tepat 11 pemain dengan ID valid.'}, status=400)


        user = request.user

        with transaction.atomic():
            if formation_id:
                formation = get_object_or_404(BestEleven, pk=formation_id, fan_account=user)
                formation.name = name
                formation.layout = layout
            else:
                formation = BestEleven.objects.create(fan_account=user, name=name, layout=layout)

            # Set relasi ManyToMany (Django ORM bisa handle UUID strings)
            formation.players.set(player_ids_for_m2m)

            # Simpan data slot ke JSONField (pastikan playerId adalah string)
            formation.player_slot_data = valid_player_ids_data

            formation.save()

        print(f"Saved formation ID {formation.id} with player_slot_data:", formation.player_slot_data)

        return JsonResponse({
            'success': True,
            'formation': {'id': formation.id, 'name': formation.name, 'layout': formation.layout},
            'message': 'Formasi berhasil disimpan!'
        })

    except Player.DoesNotExist:
         print(traceback.format_exc())
         return JsonResponse({'error': 'Satu atau lebih ID pemain tidak valid.'}, status=400)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'Gagal menyimpan formasi: {str(e)}'}, status=500)
# --- AKHIR PERBARUAN save_formation_api ---

# --- PERBARUI FUNGSI get_formation_details_api ---
@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def get_formation_details_api(request, pk):
    """ API Endpoint: Ambil detail formasi (GET) atau Hapus formasi (DELETE), handle UUID. """

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized: User not logged in.'}, status=401)

    try:
        formation = get_object_or_404(
            BestEleven, # Cukup ambil BestEleven object
            pk=pk,
            fan_account=request.user
        )
    except BestEleven.DoesNotExist:
        return JsonResponse({'error': 'Formation not found or access denied.'}, status=404)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)


    if request.method == 'DELETE':
        # ... (Logika DELETE SAMA) ...
        try:
            formation_name = formation.name
            formation.delete()
            return HttpResponse(status=204)
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'error': f'Failed to delete formation: {str(e)}'}, status=500)

    elif request.method == 'GET':
        saved_slot_data = formation.player_slot_data or []
        print(f"[GET /api/formation/{pk}/] Raw saved_slot_data:", saved_slot_data)

        players_data = []
        player_uuid_strings_in_json = []

        # Validasi format dasar dan kumpulkan ID (sebagai string)
        valid_slot_items = []
        for item in saved_slot_data:
            if isinstance(item, dict) and 'playerId' in item and 'slotId' in item:
                 player_id_str = item.get('playerId')
                 slot_id_str = item.get('slotId')
                 # Validasi sederhana UUID string (bukan validasi penuh, tapi cukup)
                 if player_id_str and isinstance(player_id_str, str) and len(player_id_str) > 30 and slot_id_str:
                     player_uuid_strings_in_json.append(player_id_str)
                     valid_slot_items.append({'playerId': player_id_str, 'slotId': slot_id_str})
                 else:
                      print(f"Warning: Invalid playerId (UUID string) or slotId format in slot data for formation {formation.id}: {item}")
            else:
                 print(f"Warning: Invalid item format in player_slot_data for formation {formation.id}: {item}")

        if not player_uuid_strings_in_json:
             print(f"Warning: No valid player UUID strings found in player_slot_data for formation {formation.id}.")
             return JsonResponse({
                 'id': formation.id, 'name': formation.name,
                 'layout': formation.layout, 'players': []
             })

        # Ambil objek Player yang relevan (Django handle UUID strings in __in)
        players_map = {str(p.id): p for p in Player.objects.filter(id__in=player_uuid_strings_in_json).prefetch_related('current_club')}
        print(f"[GET /api/formation/{pk}/] Players found in DB (UUID Strings):", list(players_map.keys()))

        # Bangun response berdasarkan item slot yang valid, gunakan string UUID untuk lookup
        for item in valid_slot_items:
             player_id_str = item['playerId'] # Ini sudah string UUID
             slot_id = item['slotId']
             player_obj = players_map.get(player_id_str) # Lookup pakai string UUID

             if player_obj:
                 player_data = {
                     # Kirim ID sebagai string ke frontend
                     'id': player_id_str,
                     'name': player_obj.nama_pemain,
                     'position': player_obj.position,
                     'market_value': player_obj.market_value or 0,
                     'nationality': player_obj.negara or '-',
                     'profile_image_url': player_obj.thumbnail or '',
                     'club_name': player_obj.current_club.name if player_obj.current_club else 'N/A',
                     'slotId': slot_id
                 }
                 players_data.append(player_data)
             else:
                 print(f"Warning: Player UUID {player_id_str} from slot data not found in Player model for formation {formation.id}.")

        print(f"[GET /api/formation/{pk}/] Final players_data to send (count: {len(players_data)}):", players_data)

        if len(players_data) != 11 and len(saved_slot_data) == 11 and len(valid_slot_items) == 11:
             print(f"Warning: Expected 11 players based on valid slot data, but only found {len(players_data)} valid player objects in DB.")


        return JsonResponse({
            'id': formation.id,
            'name': formation.name,
            'layout': formation.layout,
            'players': players_data
        })

    return HttpResponse(status=405)