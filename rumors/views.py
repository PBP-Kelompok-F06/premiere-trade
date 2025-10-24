from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from rumors.models import Rumors
from rumors.forms import RumorsForm
from main.models import Player
from accounts.models import Profile
from django.http import HttpResponseForbidden


# ========== Menampilkan semua rumors ==========
def show_rumors_main(request):
    filter_type = request.GET.get("filter", "all")

    if filter_type == "all":
        rumors_list = Rumors.objects.all().order_by('-created_at')
    else:
        rumors_list = Rumors.objects.filter(author=request.user).order_by('-created_at')

    context = {
        'rumors_list': rumors_list,
        'last_login': request.COOKIES.get('last_login', 'Never'),
    }
    return render(request, "rumors_main.html", context)

# ========== Detail rumor ==========
def show_rumors_detail(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    rumor.increment_views()
    context = {'rumor': rumor}
    return render(request, "rumors_detail.html", context)

# ========== Membuat rumor ==========
@login_required(login_url='accounts:login_page')
def create_rumors(request):
    # 🔒 Cegah admin club bikin rumor
    if request.user.is_club_admin:
        messages.error(request, "Club admins are not allowed to create rumors.")
        return redirect('rumors:show_rumors_main')

    if request.method == "POST":
        form = RumorsForm(request.POST)
        if form.is_valid():
            rumor = form.save(commit=False)
            rumor.author = request.user
            rumor.save()
            messages.success(request, "Rumor successfully created!")
            return redirect('rumors:show_rumors_main')
        else:
            print("DEBUG FORM ERRORS:", form.errors)
    else:
        form = RumorsForm()

    context = {'form': form}
    return render(request, "create_rumors.html", context)

# ========== Mengedit rumor ==========
@login_required(login_url='accounts:login_page')
def edit_rumors(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    if rumor.author != request.user:
        return HttpResponse("Kamu tidak punya izin mengedit rumor ini.", status=403)

    form = RumorsForm(request.POST or None, instance=rumor)
    if form.is_valid():
        form.save()
        messages.success(request, "Rumor berhasil diupdate!")
        return redirect('rumors:show_rumors_detail', id=id)
    return render(request, "edit_rumors.html", {'form': form, 'rumor': rumor})

# ========== Menghapus rumor ==========
@login_required(login_url='accounts:login_page')
def delete_rumors(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    if rumor.author != request.user:
        return HttpResponse("Kamu tidak punya izin menghapus rumor ini.", status=403)
    rumor.delete()
    messages.success(request, "Rumor berhasil dihapus.")
    return redirect('rumors:show_rumors_main')

# ========== Verifikasi oleh admin ==========
@login_required(login_url='accounts:login_page')
def verify_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    # Cek kalau user bukan admin club
    if not request.user.is_club_admin:
        return HttpResponseForbidden("You are not authorized to verify rumors.")


    # Ambil profile user
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You don't have a club assigned to your profile.")
        return redirect('rumors:show_rumors_detail', id=id)

    # Cek apakah rumor ini menuju club yang dikelola oleh admin tersebut
    if profile.managed_club != rumor.club_tujuan:
        messages.error(request, "You can only verify rumors directed to your managed club.")
        return redirect('rumors:show_rumors_detail', id=id)

    # Jika lolos semua, verifikasi rumor
    rumor.is_verified = True
    rumor.save()
    messages.success(request, f"Rumor '{rumor.title}' has been verified successfully!")
    return redirect('rumors:show_rumors_detail', id=id)

# ========== AJAX: get pemain berdasarkan club_asal ==========
def get_players_by_club(request):
    club_id = request.GET.get('club_id')
    players = Player.objects.filter(current_club_id=club_id).values('id', 'nama_pemain')
    return JsonResponse(list(players), safe=False)
