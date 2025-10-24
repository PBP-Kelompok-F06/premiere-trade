from django.urls import path
from . import views

# Ini penting agar kita bisa memanggil URL 
# seperti 'accounts:login_ajax'
app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    
    path('register-ajax/', views.register_ajax, name='register_ajax'),
    path('login-ajax/', views.login_ajax, name='login_ajax'),
    
    path('logout/', views.logout_user, name='logout_user'),
    
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.superuser_dashboard, name='superuser_dashboard'),
    path('user/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('user/add/', views.add_user, name='add_user'),
    path('profile/delete/', views.delete_account, name='delete_account'),
]