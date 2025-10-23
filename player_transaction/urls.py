from django.urls import path
from . import views

# Ini penting agar kita bisa memanggil URL 
# seperti 'accounts:login_ajax'
app_name = 'player_transaction'

urlpatterns = [
    # URL untuk halaman HTML
    path('pemain_dijual/', views.menampilkan_list_pemain_yang_sedang_dijual, name='pemain_dijual'),
    path('club_saya/', views.list_pemain_saya, name='club_saya'),
    path('jual/<uuid:player_id>/', views.jual_pemain_ajax, name='jual_pemain_ajax'),
    path('batalkan-jual/<uuid:player_id>/', views.batalkan_jual_pemain_ajax, name='batalkan_jual_pemain_ajax'),
    path('beli/<uuid:player_id>/', views.beli_pemain_ajax, name='beli_pemain_ajax'),
    path('inbox/', views.negotiation_inbox, name='negotiation_inbox'),
    path('send-negotiation/<uuid:player_id>/', views.send_negotiation, name='send_negotiation'),
    path('negotiation/<int:nego_id>/<str:action>/', views.respond_negotiation, name='respond_negotiation'),
]