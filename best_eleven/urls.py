from django.urls import path
from .views import (
    get_builder_data,
    get_players_by_club_api,
    save_formation_api,
    get_formation_details_api,
)
from django.views.generic import TemplateView

app_name = 'best_eleven'

urlpatterns = [
    path('', TemplateView.as_view(template_name="besteleven_builder.html"), name='team_builder'),
    path('api/builder-data/', get_builder_data, name='api_builder_data'),
    path('api/get-players/', get_players_by_club_api, name='api_get_players'),
    path('api/save-formation/', save_formation_api, name='api_save_formation'),
    path('api/formation/<int:pk>/', get_formation_details_api, name='api_get_formation_details'),
]