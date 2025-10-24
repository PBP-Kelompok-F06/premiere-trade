from django.urls import path
from rumors import views

app_name = 'rumors'

urlpatterns = [
    path('', views.show_rumors_main, name="show_rumors_main"),  # /rumors/
    path('create/', views.create_rumors, name="create_rumors"),  # /rumors/create/
    path('<uuid:id>/', views.show_rumors_detail, name="show_rumors_detail"),  # /rumors/<uuid>/
    path('<uuid:id>/edit/', views.edit_rumors, name='edit_rumors'),  # /rumors/<uuid>/edit/
    path('<uuid:id>/delete/', views.delete_rumors, name='delete_rumors'),  # /rumors/<uuid>/delete/
    path('<uuid:id>/verify/', views.verify_rumor, name='verify_rumor'),  # /rumors/<uuid>/verify/
    path('get-players/', views.get_players_by_club, name='get_players_by_club'),  # /rumors/get-players/
    path('<uuid:id>/deny/', views.deny_rumor, name='deny_rumor'),
    path('<uuid:id>/revert/', views.revert_rumor, name='revert_rumor'),
]
