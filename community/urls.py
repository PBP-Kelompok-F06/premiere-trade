# community/urls.py

from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_index, name='community_home'),
    path('reply/<int:post_id>/', views.add_reply, name='add_reply'),
    path('nested-reply/<int:reply_id>/', views.add_nested_reply, name='add_nested_reply'),  # ✅ ROUTE BARU
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
]