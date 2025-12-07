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
    path('json/', views.show_json, name='show_json'),
    path('json/<int:id>/', views.show_json_by_id, name='show_json_by_id'),
    path('add/', views.add_post, name='add_post'),
    path('add-flutter/', views.add_post_flutter, name='add_post_flutter'),
    path('edit-flutter/<int:post_id>/', views.edit_post_flutter, name='edit_post_flutter'),
    path('delete-flutter/<int:post_id>/', views.delete_post_flutter, name='delete_post_flutter'),
    path('reply-flutter/<int:post_id>/', views.add_reply_flutter, name='add_reply_flutter'),
    path('nested-reply-flutter/<int:reply_id>/', views.add_nested_reply_flutter, name='add_nested_reply_flutter'),
    path('json-flutter/', views.show_json_flutter, name='show_json_flutter'),
    path('json-flutter/<int:id>/', views.show_json_by_id_flutter, name='show_json_by_id_flutter'),
    path('json-flutter/<int:post_id>/replies/', views.show_replies_json_flutter, name='show_replies_json_flutter'),
    path('json-flutter/<int:reply_id>/nested-replies/', views.show_nested_replies_json_flutter, name='show_nested_replies_json_flutter'),
]