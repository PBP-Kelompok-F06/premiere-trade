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
    #  Cegah admin club bikin rumor
    if request.user.is_club_admin:
        return redirect('rumors:show_rumors_main')

    if request.method == "POST":
        form = RumorsForm(request.POST)
        if form.is_valid():
            rumor = form.save(commit=False)
            rumor.author = request.user
            rumor.save()
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
        return HttpResponse("You are not authorized to edit this rumor.", status=403)

    original_data = {
        "club_asal": rumor.club_asal,
        "club_tujuan": rumor.club_tujuan,
        "pemain": rumor.pemain,
        "content": rumor.content,
    }

    form = RumorsForm(request.POST or None, instance=rumor)

    if request.method == "POST":
        if form.is_valid():
            updated_rumor = form.save(commit=False)

            # Cek apakah ada perubahan pada data utama
            data_changed = (
                updated_rumor.club_asal != original_data["club_asal"] or
                updated_rumor.club_tujuan != original_data["club_tujuan"] or
                updated_rumor.pemain != original_data["pemain"] or
                updated_rumor.content != original_data["content"]
            )

            #  Reset status hanya jika ada perubahan dan status lama bukan pending
            if data_changed and rumor.status in ["verified", "denied"]:
                updated_rumor.status = "pending"
                messages.warning(
                    request,
                    "Editing this rumor has reset its verification status back to Pending for re-verification."
                )
            elif not data_changed:
                messages.info(request, "No changes detected. Status remains unchanged.")

            updated_rumor.save()
            return redirect('rumors:show_rumors_detail', id=id)
        else:
            messages.error(request, "Please fix the errors in the form before submitting.")

    context = {'form': form, 'rumor': rumor}
    return render(request, "edit_rumors.html", context)


# ========== Menghapus rumor ==========
@login_required(login_url='accounts:login_page')
def delete_rumors(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    if rumor.author != request.user:
        return HttpResponse("Kamu tidak punya izin menghapus rumor ini.", status=403)
    rumor.delete()
    
    return redirect('rumors:show_rumors_main')

# ========== Verifikasi oleh admin ==========
@login_required(login_url='accounts:login_page')
def verify_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    # Hanya admin klub tujuan atau asal yang bisa verifikasi
    if not request.user.is_club_admin:
        
        return redirect('rumors:show_rumors_detail', id=id)

    profile = getattr(request.user, "profile", None)
    if not profile or not profile.managed_club:
        
        return redirect('rumors:show_rumors_detail', id=id)

    if profile.managed_club not in [rumor.club_tujuan, rumor.club_asal]:
        
        return redirect('rumors:show_rumors_detail', id=id)

    # Update status ke verified
    rumor.status = "verified"
    rumor.save()
    
    return redirect('rumors:show_rumors_detail', id=id)

# ========== AJAX: get pemain berdasarkan club_asal ==========
def get_players_by_club(request):
    club_id = request.GET.get('club_id')
    players = Player.objects.filter(current_club_id=club_id).values('id', 'nama_pemain')
    return JsonResponse(list(players), safe=False)

@login_required(login_url='accounts:login_page')
def deny_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    if not request.user.is_club_admin:
        
        return redirect('rumors:show_rumors_detail', id=id)

    profile = getattr(request.user, "profile", None)
    if not profile or not profile.managed_club:

        return redirect('rumors:show_rumors_detail', id=id)

    if profile.managed_club not in [rumor.club_tujuan, rumor.club_asal]:
        
        return redirect('rumors:show_rumors_detail', id=id)

    # Update status ke denied
    rumor.status = "denied"
    rumor.save()
    
    return redirect('rumors:show_rumors_detail', id=id)

@login_required(login_url='accounts:login_page')
def revert_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    # Hanya admin klub yang bisa revert
    if not request.user.is_club_admin:

        return redirect('rumors:show_rumors_detail', id=id)

    profile = getattr(request.user, "profile", None)
    if not profile or not profile.managed_club:
        
        return redirect('rumors:show_rumors_detail', id=id)

    # Hanya admin klub tujuan atau asal yang bisa revert
    if profile.managed_club not in [rumor.club_tujuan, rumor.club_asal]:
        
        return redirect('rumors:show_rumors_detail', id=id)

    #  Set status jadi pending lagi
    rumor.status = "pending"
    rumor.save()
    
    return redirect('rumors:show_rumors_detail', id=id)
