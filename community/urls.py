# community/urls.py

from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_index, name='community_home'),
    path('reply/<int:post_id>/', views.add_reply, name='add_reply'),
]