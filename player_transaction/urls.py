from django.urls import path
from . import views

# Ini penting agar kita bisa memanggil URL 
# seperti 'accounts:login_ajax'
app_name = 'player_transaction'

urlpatterns = [
    # URL untuk halaman HTML
    path("list_pemain_dijual/", views.list_pemain_dijual_view, name="list_pemain_dijual"),
    path("api/list_pemain_dijual/", views.list_pemain_dijual_json, name="list_pemain_dijual_json"),
    path("club_saya/", views.club_saya_view, name="club_saya"),
    path("api/list_pemain_saya/", views.list_pemain_saya, name="list_pemain_saya"),
    path('jual/<uuid:player_id>/', views.jual_pemain_ajax, name='jual_pemain_ajax'),
    path('batalkan-jual/<uuid:player_id>/', views.batalkan_jual_pemain_ajax, name='batalkan_jual_pemain_ajax'),
    path('beli/<uuid:player_id>/', views.beli_pemain_ajax, name='beli_pemain_ajax'),
    path('inbox/', views.negotiation_inbox, name='negotiation_inbox'),
    path('send-negotiation/<uuid:player_id>/', views.send_negotiation, name='send_negotiation'),
    path('negotiation/<int:nego_id>/<str:action>/', views.respond_negotiation, name='respond_negotiation'),



    path('show_xml/', views.show_xml, name='show_xml'),
    path('show_json/', views.show_json, name='show_json'),
    path('show_xml_by_id/<uuid:player_id>/', views.show_xml_by_id, name='show_xml_by_id'),
    path('show_json_by_id/<uuid:player_id>/', views.show_json_by_id, name='show_json_by_id'),
]