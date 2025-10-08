from django.urls import path
from players.views import show_main

app_name = 'players'

urlpatterns = [
    path('', show_main, name='show_main'),
]