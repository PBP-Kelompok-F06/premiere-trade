import json
import traceback
import uuid
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST 
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.db import transaction

from main.models import Player, Club
from .models import BestEleven
from .forms import BestElevenForm


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BestElevenBuilderView(LoginRequiredMixin, TemplateView):
    template_name = 'best_eleven/besteleven_builder.html'
    login_url = '/admin/login/' # <-- Redirect ke sini

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['load_formation_id'] = self.request.GET.get('load', None)
        context['show_detail_id'] = self.request.GET.get('show_detail', None)
        return context

# CBV lainnya (Detail, Delete, Update) tetap sama...
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
    success_url = reverse_lazy('best_eleven:besteleven-list') # Ganti jika perlu
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
@require_http_methods(['GET']) # **** TAMBAHKAN DECORATOR INI ****
def get_builder_data(request):
    try:
        clubs = Club.objects.order_by('name')
        club_list = [{'id': c.id, 'name': c.name} for c in clubs]
        formations = BestEleven.objects.filter(fan_account=request.user).order_by('-updated_at')
        formation_history = [{'id': f.id, 'name': f.name, 'layout': f.layout} for f in formations]
        return JsonResponse({'clubs': club_list, 'history': formation_history})
    except Exception:
        print(traceback.format_exc())
        return JsonResponse({'error': 'Gagal memuat data awal.'}, status=500)

@login_required
@require_http_methods(['GET']) # **** TAMBAHKAN DECORATOR INI ****
def get_players_by_club_api(request):
    try:
        club_id = request.GET.get('club_id')
        player_qs = Player.objects.prefetch_related('current_club')
        players = player_qs.filter(current_club_id=club_id) if club_id else player_qs.all()
        player_list = [
            {
                'id': str(p.id), 'name': p.nama_pemain,
                'club_name': p.current_club.name if p.current_club else 'N/A',
                'position': p.position, 'nationality': p.negara or '-',
                'market_value': p.market_value or 0,
                'profile_image_url': p.thumbnail or '',
            } for p in players
        ]
        return JsonResponse({'players': player_list})
    except Exception:
        print(traceback.format_exc())
        return JsonResponse({'error': 'Gagal memuat daftar pemain.'}, status=500)

# save_formation_api sudah pakai require_http_methods(["POST"]), tidak perlu diubah
@login_required
@require_POST # Alternatif lebih singkat untuk @require_http_methods(["POST"])
def save_formation_api(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        layout = data.get('layout')
        player_ids_data = data.get('player_ids')
        formation_id = data.get('formation_id')

        if not all([name, layout, player_ids_data]) or len(player_ids_data) != 11:
            return JsonResponse({'error': 'Nama, layout, dan 11 pemain wajib diisi.'}, status=400)

        valid_player_ids_data_for_json = []
        player_uuids_for_m2m = []
        for item in player_ids_data:
            player_id_str = item.get('playerId')
            slot_id_str = item.get('slotId')
            if player_id_str and slot_id_str:
                try:
                    player_uuid = uuid.UUID(player_id_str)
                    valid_player_ids_data_for_json.append({'playerId': player_id_str, 'slotId': slot_id_str})
                    player_uuids_for_m2m.append(player_uuid)
                except ValueError: print(f"Invalid UUID format: {player_id_str}")
            else: print(f"Incomplete slot data: {item}")

        if len(valid_player_ids_data_for_json) != 11:
            return JsonResponse({'error': 'Harus ada tepat 11 pemain dengan ID dan Slot valid.'}, status=400)

        user = request.user
        with transaction.atomic():
            if formation_id:
                formation = get_object_or_404(BestEleven, pk=formation_id, fan_account=user)
                formation.name = name
                formation.layout = layout
            else:
                formation = BestEleven.objects.create(fan_account=user, name=name, layout=layout)

            players_to_set = Player.objects.filter(id__in=player_uuids_for_m2m)
            if players_to_set.count() != 11:
                found_uuids = {p.id for p in players_to_set}
                missing_uuids = [str(u) for u in player_uuids_for_m2m if u not in found_uuids]
                raise Player.DoesNotExist(f"Pemain tidak ditemukan: {', '.join(missing_uuids)}")

            formation.players.set(players_to_set)
            formation.player_slot_data = valid_player_ids_data_for_json
            formation.save()

        return JsonResponse({
            'success': True,
            'formation': {'id': formation.id, 'name': formation.name, 'layout': formation.layout},
            'message': 'Formasi berhasil disimpan!'
        })
    except Player.DoesNotExist as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'Gagal menyimpan: {str(e)}'}, status=400)
    except ValueError as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'Format ID Pemain tidak valid: {str(e)}'}, status=400)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'Gagal menyimpan formasi: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def get_formation_details_api(request, pk):
    try:
        formation = get_object_or_404(BestEleven, pk=pk, fan_account=request.user)
        if request.method == 'DELETE':
            try:
                formation.delete()
                return HttpResponse(status=204)
            except Exception as e:
                print(traceback.format_exc())
                return JsonResponse({'error': f'Failed to delete formation: {str(e)}'}, status=500)

        elif request.method == 'GET':
            try:
                saved_slot_data = formation.player_slot_data or []
                players_data = []
                valid_slot_items = []
                for item in saved_slot_data:
                    if isinstance(item, dict) and 'playerId' in item and 'slotId' in item:
                        player_id_str = item['playerId']
                        slot_id_str = item['slotId']
                        try:
                            uuid.UUID(player_id_str)
                            valid_slot_items.append({'playerId': player_id_str, 'slotId': slot_id_str})
                        except ValueError: print(f"Skipping invalid UUID in slot data: {player_id_str}")
                if valid_slot_items:
                    player_ids = [item['playerId'] for item in valid_slot_items]
                    players_map = { str(p.id): p for p in Player.objects.filter(id__in=player_ids).prefetch_related('current_club')}
                    for item in valid_slot_items:
                        player_obj = players_map.get(item['playerId'])
                        if player_obj:
                            players_data.append({
                                'id': item['playerId'], 'name': player_obj.nama_pemain,
                                'position': player_obj.position, 'market_value': player_obj.market_value or 0,
                                'nationality': player_obj.negara or '-', 'profile_image_url': player_obj.thumbnail or '',
                                'club_name': player_obj.current_club.name if player_obj.current_club else 'N/A',
                                'slotId': item['slotId']
                            })
                        else: print(f"Player object not found in map for ID: {item['playerId']}")
                return JsonResponse({
                    'id': formation.id, 'name': formation.name,
                    'layout': formation.layout, 'players': players_data
                })
            except Exception as e:
                print(traceback.format_exc())
                return JsonResponse({'error': f'Error processing formation details: {str(e)}'}, status=500)
        return HttpResponse(status=405)
    except Http404:
        return JsonResponse({'error': 'Formation not found or access denied.'}, status=404)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)