from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import BestEleven
from .forms import BestElevenForm
from django.contrib.auth.models import User 

class BestElevenCreateView(CreateView):
    model = BestEleven
    form_class = BestElevenForm
    template_name = 'besteleven_form.html'
    success_url = reverse_lazy('besteleven-list') 

    def form_valid(self, form):
        try:
            default_user = User.objects.get(id=1)
            form.instance.fan_account = default_user
        except User.DoesNotExist:
            raise Exception("Tolong jalankan 'python manage.py createsuperuser' dulu.")
            
        return super().form_valid(form)
    
class BestElevenListView(ListView):
    model = BestEleven
    template_name = 'besteleven_list.html'
    context_object_name = 'besteleven_list'

    def get_queryset(self):
        return BestEleven.objects.all() 

class BestElevenDetailView(DetailView):
    model = BestEleven
    template_name = 'besteleven_detail.html'
    context_object_name = 'formasi' 

    def get_queryset(self):
        return BestEleven.objects.all()

class BestElevenUpdateView(UpdateView):
    model = BestEleven
    form_class = BestElevenForm
    template_name = 'besteleven_form.html' 
    
    def get_queryset(self):
        return BestEleven.objects.all()
    
    def get_success_url(self):
        return reverse_lazy('besteleven-detail', kwargs={'pk': self.object.pk})

class BestElevenDeleteView(DeleteView):
    model = BestEleven
    template_name = 'besteleven_confirm_delete.html'
    success_url = reverse_lazy('besteleven-list')
    
    def get_queryset(self):
        return BestEleven.objects.all()