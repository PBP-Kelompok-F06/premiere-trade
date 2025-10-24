from django.urls import path 
from .views import (
    BestElevenBuilderView, 
    BestElevenListView,    
    BestElevenDetailView, 
    FormationDeleteView,   
    BestElevenUpdateView,
    # API Views
    get_builder_data,
    get_players_by_club_api,
    save_formation_api,
    get_formation_details_api,
)

app_name = 'best_eleven'

urlpatterns = [
    path('', BestElevenBuilderView.as_view(), name='team_builder'),
    path('list/', BestElevenListView.as_view(), name='besteleven-list'),
    path('<int:pk>/', BestElevenDetailView.as_view(), name='besteleven-detail'),
    path('<int:pk>/delete/', FormationDeleteView.as_view(), name='besteleven-delete'),
    path('<int:pk>/update/', BestElevenUpdateView.as_view(), name='besteleven-update'),
    path('api/builder-data/', get_builder_data, name='api_builder_data'),
    path('api/get-players/', get_players_by_club_api, name='api_get_players'),
    path('api/save-formation/', save_formation_api, name='api_save_formation'),
    path('api/formation/<int:pk>/', get_formation_details_api, name='api_get_formation_details'),
]
