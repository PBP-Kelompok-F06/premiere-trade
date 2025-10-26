from django.urls import path
from rumors import views

app_name = 'rumors'

urlpatterns = [
    path('', views.show_rumors_main, name="show_rumors_main"), 
    path('create/', views.create_rumors, name="create_rumors"),  
    path('<uuid:id>/', views.show_rumors_detail, name="show_rumors_detail"),  
    path('<uuid:id>/edit/', views.edit_rumors, name='edit_rumors'),  
    path('<uuid:id>/delete/', views.delete_rumors, name='delete_rumors'),  
    path('<uuid:id>/verify/', views.verify_rumor, name='verify_rumor'),  
    path('get-players/', views.get_players_by_club, name='get_players_by_club'),  
    path('<uuid:id>/deny/', views.deny_rumor, name='deny_rumor'),
    path('<uuid:id>/revert/', views.revert_rumor, name='revert_rumor'),
     path('get-designated-clubs/', views.get_available_designated_clubs, name='get_designated_clubs'),
]
