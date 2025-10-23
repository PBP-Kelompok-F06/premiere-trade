from django.urls import path
from . import views  

app_name = 'best_eleven' 

urlpatterns = [
    path('', views.BestElevenBuilderView.as_view(), name='team_builder'),
    path('api/builder-data/', views.get_builder_data, name='api_builder_data'),
    path('api/get-players/', views.get_players_by_club_api, name='api_get_players'),
    path('api/save-formation/', views.save_formation_api, name='api_save_formation'),
    path('api/formation/<int:pk>/', views.get_formation_details_api, name='api_get_formation_details'),
]