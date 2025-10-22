from django.urls import path
from . import views

# Ini penting agar kita bisa memanggil URL 
# seperti 'accounts:login_ajax'
app_name = 'accounts'

urlpatterns = [
    # URL untuk halaman HTML
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    
    # URL untuk endpoint AJAX
    path('register-ajax/', views.register_ajax, name='register_ajax'),
    path('login-ajax/', views.login_ajax, name='login_ajax'),
    
    # URL untuk logout
    path('logout/', views.logout_user, name='logout_user'),
]