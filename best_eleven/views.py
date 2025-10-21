# best_eleven/views.py
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
# HAPUS BARIS INI: from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import BestEleven
from .forms import BestElevenForm
from django.contrib.auth.models import User # <-- TAMBAHKAN IMPORT INI

# --- CreateView ---
# HAPUS "LoginRequiredMixin" DARI SINI
class BestElevenCreateView(CreateView):
    model = BestEleven
    form_class = BestElevenForm
    template_name = 'besteleven_form.html'
    success_url = reverse_lazy('besteleven-list') 

    def form_valid(self, form):
        """
        Ini adalah bagian 'hack' untuk testing.
        Karena tidak ada user yang login (request.user adalah AnonymousUser),
        kita tidak bisa mengaturnya sebagai 'fan_account'.
        
        Sebagai gantinya, kita akan paksa semua formasi baru
        untuk dimiliki oleh user pertama di database (biasanya admin/superuser kamu, ID=1).
        
        PASTIKAN KAMU SUDAH MENJALANKAN "manage.py createsuperuser"
        """
        try:
            # UBAH BAGIAN INI:
            default_user = User.objects.get(id=1)
            form.instance.fan_account = default_user
        except User.DoesNotExist:
            # Ini terjadi jika kamu belum membuat superuser
            # Ini akan menyebabkan error, tapi setidaknya errornya jelas
            raise Exception("Tolong jalankan 'python manage.py createsuperuser' dulu.")
            
        return super().form_valid(form)

# --- ListView ---
# HAPUS "LoginRequiredMixin" DARI SINI
class BestElevenListView(ListView):
    model = BestEleven
    template_name = 'besteleven_list.html'
    context_object_name = 'besteleven_list'

    def get_queryset(self):
        # UBAH BARIS INI:
        # return BestEleven.objects.filter(fan_account=self.request.user)
        # MENJADI INI:
        return BestEleven.objects.all() # Tampilkan semua formasi

# --- DetailView ---
# HAPUS "LoginRequiredMixin" DARI SINI
class BestElevenDetailView(DetailView):
    model = BestEleven
    template_name = 'besteleven_detail.html'
    context_object_name = 'formasi' 

    def get_queryset(self):
        # UBAH BARIS INI:
        # return BestEleven.objects.filter(fan_account=self.request.user)
        # MENJADI INI:
        return BestEleven.objects.all()

# --- UpdateView ---
# HAPUS "LoginRequiredMixin" DARI SINI
class BestElevenUpdateView(UpdateView):
    model = BestEleven
    form_class = BestElevenForm
    template_name = 'besteleven_form.html' 
    
    def get_queryset(self):
        # UBAH BARIS INI:
        # return BestEleven.objects.filter(fan_account=self.request.user)
        # MENJADI INI:
        return BestEleven.objects.all()
    
    def get_success_url(self):
        return reverse_lazy('besteleven-detail', kwargs={'pk': self.object.pk})

# --- DeleteView ---
# HAPUS "LoginRequiredMixin" DARI SINI
class BestElevenDeleteView(DeleteView):
    model = BestEleven
    template_name = 'besteleven_confirm_delete.html'
    success_url = reverse_lazy('besteleven-list')
    
    def get_queryset(self):
        # UBAH BARIS INI:
        # return BestEleven.objects.filter(fan_account=self.request.user)
        # MENJADI INI:
        return BestEleven.objects.all()