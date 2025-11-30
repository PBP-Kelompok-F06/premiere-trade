# premiere_trade/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')), 
    path('community/', include('community.urls')), 
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('player_transaction/', include('player_transaction.urls')),
    path('rumors/', include(('rumors.urls', 'rumors'), namespace='rumors')),       
    path('player_transaction/', include('player_transaction.urls')),    
    path("accounts/", include("accounts.urls")),          
    path('best_eleven/', include('best_eleven.urls')),    
    path('auth/', include('authentication.urls')),
]