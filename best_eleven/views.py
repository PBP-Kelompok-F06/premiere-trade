from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Player, Club, BestEleven
from django.contrib.auth.models import User

def get_builder_data(request):
    try:
        clubs = Club.objects.order_by('name')
        club_list = [{'id': club.id, 'name': club.name} for club in clubs]

        try:
            user = User.objects.get(id=1)
            formations = BestEleven.objects.filter(fan_account=user).order_by('-created_at')
            formation_history = [
                {'id': f.id, 'name': f.name, 'layout': f.layout}
                for f in formations
            ]
        except User.DoesNotExist:
            formation_history = []

        return JsonResponse({
            'clubs': club_list,
            'history': formation_history
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_players_by_club_api(request):
    club_id = request.GET.get('club_id')
    if not club_id:
        return JsonResponse({'error': 'Parameter club_id needed'}, status=400)

    try:
        players = Player.objects.filter(club_id=club_id).select_related('club').order_by('name') # Efficient query
        player_list = []
        for player in players:
            player_list.append({
                'id': player.id,
                'name': player.name,
                'position_code': player.position, # GK, DEF, MID, FWD
                'position_display': player.get_position_display(), # Goalkeeper, Defender, etc.
                'market_value': player.market_value or 'N/A',
                'nationality': player.nationality or 'N/A', # Add nationality
                'profile_image_url': player.profile_image_url or '' # Default empty string
            })
        return JsonResponse({'players': player_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt 
def save_formation_api(request):
    """ API (POST) - Saves a new formation """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            formation_name = data.get('name')
            layout = data.get('layout')
            player_ids = data.get('player_ids') 

            if not all([formation_name, layout, player_ids]) or len(player_ids) != 11:
                return JsonResponse({'error': 'Incomplete data or incorrect player count (must be 11)'}, status=400)

            try:
                user = User.objects.get(id=1)
            except User.DoesNotExist:
                 return JsonResponse({'error': 'Default user (ID=1) not found. Run createsuperuser.'}, status=500)

            valid_players = Player.objects.filter(id__in=player_ids)
            if valid_players.count() != 11:
                 invalid_ids = set(player_ids) - set(valid_players.values_list('id', flat=True))
                 return JsonResponse({'error': f'Invalid player IDs found: {list(invalid_ids)}'}, status=400)

            new_formation = BestEleven(
                fan_account=user,
                name=formation_name,
                layout=layout
            )
            new_formation.save() 
            new_formation.players.set(valid_players) 
            return JsonResponse({
                'success': True,
                'formation_id': new_formation.id,
                'message': 'Formation saved successfully!'
                }, status=201) 
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An internal error occurred: {e}'}, status=500)
    else:
        return JsonResponse({'error': 'POST method required'}, status=405) 

def get_formation_details_api(request, pk):
    try:
        formation = BestEleven.objects.prefetch_related('players').get(pk=pk, fan_account_id=1)

        player_list = []
        for player in formation.players.all():
             player_list.append({
                'id': player.id,
                'name': player.name,
                'position_code': player.position,
                'position_display': player.get_position_display(),
                'market_value': player.market_value or 'N/A',
                'nationality': player.nationality or 'N/A',
                'profile_image_url': player.profile_image_url or '',
                'club_name': player.club.name if player.club else 'N/A'
            })

        return JsonResponse({
            'id': formation.id,
            'name': formation.name,
            'layout': formation.layout,
            'players': player_list
        })
    except BestEleven.DoesNotExist:
        return JsonResponse({'error': 'Formation not found or access denied'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)