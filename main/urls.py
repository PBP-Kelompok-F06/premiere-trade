from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('club/<int:club_id>/players/', views.player_list_by_club, name='player_list_by_club'),

]