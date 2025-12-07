from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('club/<int:club_id>/players/', views.player_list_by_club, name='player_list_by_club'),

    path('api/clubs/', views.show_clubs_json, name='show_clubs_json'),
    path('api/club/<int:club_id>/players/', views.show_players_by_club_json, name='show_players_by_club_json'),
]