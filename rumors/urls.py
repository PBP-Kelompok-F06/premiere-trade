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
    path('json/', views.get_rumors_json, name='get_rumors_json'),
    path('create-flutter/', views.create_rumor_flutter, name='create_rumor_flutter'),
    path('<uuid:id>/verify-flutter/', views.verify_rumor_flutter, name='verify_rumor_flutter'),
    path('<uuid:id>/deny-flutter/', views.deny_rumor_flutter, name='deny_rumor_flutter'),
    path('<uuid:id>/delete-flutter/', views.delete_rumor_flutter, name='delete_rumor_flutter'),
    path('<uuid:id>/edit-flutter/', views.edit_rumor_flutter, name='edit_rumor_flutter'),
    path('<uuid:id>/revert-flutter/', views.revert_rumor_flutter, name='revert_rumor_flutter'),
    path('get-user-role/', views.get_user_role, name='get_user_role'),
]
