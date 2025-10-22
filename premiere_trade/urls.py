# premiere_trade/urls.py

from django.contrib import admin
from django.urls import path, include
# JANGAN impor views dari community di sini

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')), 
    path('community/', include('community.urls')), 
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('main.urls', namespace='main')),
    path('best-eleven/', include('best_eleven.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]