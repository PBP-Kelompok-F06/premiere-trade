from django.urls import path
from .views import (
    BestElevenCreateView, 
    BestElevenListView, 
    BestElevenDetailView,
    BestElevenUpdateView,
    BestElevenDeleteView  
) 

urlpatterns = [
    path('', BestElevenListView.as_view(), name='besteleven-list'),
    path('create/', BestElevenCreateView.as_view(), name='besteleven-create'),
    path('<int:pk>/', BestElevenDetailView.as_view(), name='besteleven-detail'),
    path('<int:pk>/update/', BestElevenUpdateView.as_view(), name='besteleven-update'),
    path('<int:pk>/delete/', BestElevenDeleteView.as_view(), name='besteleven-delete'),
]