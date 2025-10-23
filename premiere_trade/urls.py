# premiere_trade/urls.py

from django.contrib import admin
from django.urls import path, include
# JANGAN impor views dari community di sini

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')), 
    path('community/', include('community.urls')), 
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('player_transaction/', include('player_transaction.urls')),
]