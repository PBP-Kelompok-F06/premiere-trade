from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rumors.models import Rumors
from rumors.forms import RumorsForm
from main.models import Player, Club
from accounts.models import Profile
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def get_user_role(request):
    is_club_admin = False
    if request.user.is_authenticated and request.user.is_club_admin:
        is_club_admin = True
    return JsonResponse({'is_club_admin': is_club_admin})

@csrf_exempt
def revert_rumor_flutter(request, id):
    if request.method == 'POST':
        try:
            rumor = Rumors.objects.get(pk=id)
            
            # Validasi Admin
            profile = getattr(request.user, "profile", None)
            if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            # Ubah status kembali ke pending
            rumor.status = "pending"
            rumor.save()
            
            return JsonResponse({"status": "success", "message": "Rumor status reverted to pending!"})
            
        except Rumors.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rumor not found"}, status=404)
            
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@csrf_exempt
def edit_rumor_flutter(request, id):
    if request.method == 'POST':
        try:
            rumor = Rumors.objects.get(pk=id)
            
            # Cek Author
            if rumor.author != request.user:
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            data = json.loads(request.body)
            
            # Ambil data baru
            new_content = data.get('content')
            new_club_asal_id = data.get('club_asal')
            new_club_tujuan_id = data.get('club_tujuan')
            new_pemain_id = data.get('pemain')

            has_changed = False

            # Logika Deteksi Perubahan 
            
            # 1. Cek Content
            if new_content is not None and rumor.content != new_content:
                rumor.content = new_content
                has_changed = True

            # 2. Cek Club Asal
            if new_club_asal_id and str(rumor.club_asal.id) != str(new_club_asal_id):
                rumor.club_asal = Club.objects.get(pk=new_club_asal_id)
                has_changed = True

            # 3. Cek Club Tujuan
            if new_club_tujuan_id and str(rumor.club_tujuan.id) != str(new_club_tujuan_id):
                rumor.club_tujuan = Club.objects.get(pk=new_club_tujuan_id)
                has_changed = True

            # 4. Cek Pemain
            if new_pemain_id and str(rumor.pemain.id) != str(new_pemain_id):
                rumor.pemain = Player.objects.get(pk=new_pemain_id)
                has_changed = True

            # Reset Status Hanya Jika Ada Perubahan 
            if has_changed:
                if rumor.status in ['verified', 'denied']:
                    rumor.status = 'pending'
                rumor.save()
                return JsonResponse({"status": "success", "message": "Rumor berhasil diupdate!"}, status=200)
            else:
                # Tidak ada perubahan, tidak perlu save
                return JsonResponse({"status": "success", "message": "Tidak ada perubahan data."}, status=200)

        except Rumors.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rumor tidak ditemukan"}, status=404)
        except Club.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Klub tidak ditemukan"}, status=404)
        except Player.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Pemain tidak ditemukan"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def verify_rumor_flutter(request, id):
    if request.method == 'POST':
        try:
            rumor = Rumors.objects.get(pk=id)
            profile = getattr(request.user, "profile", None)
            if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            rumor.status = "verified"
            rumor.save()
            return JsonResponse({"status": "success", "message": "Rumor verified!"})
        except Rumors.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rumor not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@csrf_exempt
def deny_rumor_flutter(request, id):
    if request.method == 'POST':
        try:
            rumor = Rumors.objects.get(pk=id)
            # Validasi Admin
            profile = getattr(request.user, "profile", None)
            if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            rumor.status = "denied"
            rumor.save()
            return JsonResponse({"status": "success", "message": "Rumor denied!"})
        except Rumors.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rumor not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@csrf_exempt
def delete_rumor_flutter(request, id):
    if request.method == 'POST':
        try:
            rumor = Rumors.objects.get(pk=id)
            # Validasi Author
            if rumor.author != request.user:
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            rumor.delete()
            return JsonResponse({"status": "success", "message": "Rumor deleted!"})
        except Rumors.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rumor not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

def get_rumors_json(request):
    rumors = Rumors.objects.all().order_by('-created_at')
    nama = request.GET.get("nama", "").strip()
    club_asal_id = request.GET.get("asal")
    club_tujuan_id = request.GET.get("tujuan")

    if nama:
        rumors = rumors.filter(pemain__nama_pemain__icontains=nama)
    
    if club_asal_id and club_asal_id != "null" and club_asal_id != "":
        try:
            rumors = rumors.filter(club_asal__id=int(club_asal_id))
        except ValueError:
            pass

    if club_tujuan_id and club_tujuan_id != "null" and club_tujuan_id != "":
        try:
            rumors = rumors.filter(club_tujuan__id=int(club_tujuan_id))
        except ValueError:
            pass
    
    user_managed_club_id = None
    if request.user.is_authenticated and request.user.is_club_admin:
        profile = getattr(request.user, "profile", None)
        if profile and profile.managed_club:
            user_managed_club_id = profile.managed_club.id

    data = []
    for rumor in rumors:
        is_relevant_admin = False
        
        # Cek hanya jika user punya managed club
        if user_managed_club_id:
            ids_involved = []
            if rumor.club_asal: ids_involved.append(rumor.club_asal.id)
            if rumor.club_tujuan: ids_involved.append(rumor.club_tujuan.id)
            
            # Jika club admin ada di salah satu (asal/tujuan), maka True
            if user_managed_club_id in ids_involved:
                is_relevant_admin = True

        data.append({
            "id": str(rumor.id),
            "title": rumor.title,
            "content": rumor.content,
            "author": rumor.author.username,
            "pemain_nama": rumor.pemain.nama_pemain,
            "pemain_id": str(rumor.pemain.id),
            "pemain_thumbnail": rumor.pemain.thumbnail if rumor.pemain.thumbnail else "https://cdn-icons-png.flaticon.com/512/149/149071.png",
            "pemain_value": rumor.pemain.market_value,
            "pemain_umur": rumor.pemain.umur,
            "pemain_posisi": rumor.pemain.position,
            "pemain_negara": rumor.pemain.negara,
            "club_asal_nama": rumor.club_asal.name if rumor.club_asal else "-",
            "club_asal_id": str(rumor.club_asal.id) if rumor.club_asal else None,
            "club_asal_logo": rumor.club_asal.logo_url if rumor.club_asal and rumor.club_asal.logo_url else "",
            "club_tujuan_nama": rumor.club_tujuan.name if rumor.club_tujuan else "-",
            "club_tujuan_id": str(rumor.club_tujuan.id) if rumor.club_tujuan else None,
            "club_tujuan_logo": rumor.club_tujuan.logo_url if rumor.club_tujuan and rumor.club_tujuan.logo_url else "",
            "status": rumor.status,
            "created_at": rumor.created_at.strftime("%Y-%m-%d %H:%M"),
            "views": rumor.rumors_views,
            "is_author": request.user == rumor.author,

            "is_admin": is_relevant_admin 
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def create_rumor_flutter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            content = data.get('content')
            club_asal_id = data.get('club_asal')
            club_tujuan_id = data.get('club_tujuan')
            pemain_id = data.get('pemain')
            if not all([content, club_asal_id, club_tujuan_id, pemain_id]):
                return JsonResponse({"status": "error", "message": "Data tidak lengkap"}, status=400)
            
            user = request.user
            club_asal = Club.objects.get(pk=club_asal_id)
            club_tujuan = Club.objects.get(pk=club_tujuan_id)
            pemain = Player.objects.get(pk=pemain_id)

            new_rumor = Rumors.objects.create(
                author=user,
                content=content,
                club_asal=club_asal,
                club_tujuan=club_tujuan,
                pemain=pemain,
                status="pending"
            )

            return JsonResponse({"status": "success", "message": "Rumor berhasil dibuat!"}, status=200)
        
        except Club.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Klub tidak ditemukan"}, status=404)
        except Player.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Pemain tidak ditemukan"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)


# ========== Menampilkan semua rumors ==========
def show_rumors_main(request):
    # Ambil query filter dari GET
    nama = request.GET.get("nama", "").strip()
    club_asal = request.GET.get("asal")
    club_tujuan = request.GET.get("tujuan")

    # Ambil semua data awal
    rumors_list = Rumors.objects.all().order_by('-created_at')

    # Terapkan filter dinamis
    if nama:
        rumors_list = rumors_list.filter(pemain__nama_pemain__icontains=nama)
    if club_asal and club_asal.isdigit():
        rumors_list = rumors_list.filter(club_asal__id=int(club_asal))
    if club_tujuan and club_tujuan.isdigit():
        rumors_list = rumors_list.filter(club_tujuan__id=int(club_tujuan))

    context = {
        'rumors_list': rumors_list,
        'clubs': Club.objects.exclude(name="Admin").order_by('name'),
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "partials/rumor_list.html", context)
    return render(request, "rumors_main.html", context)

    
# ========== Detail rumor ==========
def show_rumors_detail(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    rumor.increment_views()

    is_authorized_admin = False
    if request.user.is_authenticated and request.user.is_club_admin:
        profile = getattr(request.user, "profile", None)
        if profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]:
            is_authorized_admin = True

    context = {
        'rumor': rumor,
        'is_authorized_admin': is_authorized_admin,
    }
    return render(request, "rumors_detail.html", context)


# ========== Membuat rumor ==========
@login_required(login_url='accounts:login_page')
def create_rumors(request):
    if request.user.is_club_admin:
        return redirect('rumors:show_rumors_main')

    if request.method == "POST":
        form = RumorsForm(request.POST)
        if form.is_valid():
            rumor = form.save(commit=False)
            rumor.author = request.user
            rumor.save()

            # AJAX response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": "✏️ Rumor berhasil dibuat! ✏️",
                    "id": str(rumor.id)
                })

            return redirect('rumors:show_rumors_main')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": "Invalid form data.",
                    "errors": form.errors
                })
    else:
        form = RumorsForm()
    
    clubs = Club.objects.exclude(name="Admin").order_by("name")

    context = {
        'form': form,
        'clubs': clubs, 
    }

    return render(request, "create_rumors.html", context)



# ========== Mengedit rumor ==========
@login_required(login_url='accounts:login_page')
def edit_rumors(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    if rumor.author != request.user:
        return HttpResponse("You are not authorized to edit this rumor.", status=403)

    form = RumorsForm(request.POST or None, instance=rumor)

    if request.method == "POST":
        if form.is_valid():
            # --- Ambil nilai lama dari database
            old_rumor = Rumors.objects.get(pk=rumor.pk)
            old_data = {
                "club_asal": str(old_rumor.club_asal.id) if old_rumor.club_asal else None,
                "club_tujuan": str(old_rumor.club_tujuan.id) if old_rumor.club_tujuan else None,
                "pemain": str(old_rumor.pemain.id) if old_rumor.pemain else None,
                "content": old_rumor.content or "",
            }

            # --- Ambil nilai baru langsung dari request.POST ---
            new_data = {
                "club_asal": request.POST.get("club_asal") or None,
                "club_tujuan": request.POST.get("club_tujuan") or None,
                "pemain": request.POST.get("pemain") or None,
                "content": request.POST.get("content", ""),
            }

            # --- Normalisasi dan bandingkan ---
            def normalize(value):
                if value is None:
                    return None
                return str(value).strip().lower()

            changed = any(
                normalize(old_data[field]) != normalize(new_data[field])
                for field in old_data
            )

            # ============ DEBUG PRINT ============
            print("=== DEBUG PERBANDINGAN DATA ===")
            for field in old_data:
                print(f"{field}: {old_data[field]}  -->  {new_data[field]}")
            print(f"changed = {changed}")
            print("===============================")
            # =====================================

            updated_rumor = form.save(commit=False)

            if changed and old_rumor.status in ["verified", "denied"]:
                updated_rumor.status = "pending"

            updated_rumor.save()

            message = (
                "✅ Rumor berhasil diperbarui!"
                if changed
                else "Tidak ada perubahan✍️"
            )



            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": message,
                    "id": str(rumor.id)
                })

            return redirect('rumors:show_rumors_detail', id=id)
        
        else:
            # ============ DEBUG FORM ERRORS ============
            print("=== FORM ERRORS ===")
            print(form.errors)
            print("====================")
            # ============================================

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": "Invalid form data.",
                    "errors": form.errors
                })

    return render(request, "edit_rumors.html", {"form": form, "rumor": rumor})





# ========== Menghapus rumor ==========
@login_required(login_url='accounts:login_page')
def delete_rumors(request, id):
    rumor = get_object_or_404(Rumors, pk=id)

    if rumor.author != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "error": "You are not authorized to delete this rumor."
            }, status=403)
        return HttpResponse("You are not authorized to delete this rumor.", status=403)

    rumor.delete()

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "message": "Rumor deleted successfully!"
        })

    return redirect('rumors:show_rumors_main')



# ========== AJAX: get pemain berdasarkan club_asal ==========
def get_players_by_club(request):
    club_id = request.GET.get('club_id')
    players = Player.objects.filter(current_club_id=club_id).values('id', 'nama_pemain')
    return JsonResponse(list(players), safe=False)


@require_GET
def get_available_designated_clubs(request):
    club_asal_id = request.GET.get('club_asal')
    print("DEBUG: get_available_designated_clubs called with club_asal_id =", club_asal_id)
    clubs = Club.objects.exclude(name="Admin")

    if club_asal_id and club_asal_id.isdigit():
        clubs = clubs.exclude(id=int(club_asal_id))
        print("DEBUG: excluding club id", club_asal_id)

    data = list(clubs.values('id', 'name'))
    print("DEBUG: returning clubs:", data)
    return JsonResponse(data, safe=False)


@login_required(login_url='accounts:login_page')
def verify_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    profile = getattr(request.user, "profile", None)

    # Pastikan user adalah admin klub asal/tujuan
    if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "error": "You are not authorized to verify this rumor."})
        messages.error(request, "You are not authorized to verify this rumor.")
        return redirect('rumors:show_rumors_detail', id=id)

    rumor.status = "verified"
    rumor.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        #menentukan isi alert di browser
        return JsonResponse({
            "success": True,
            "status": rumor.status,
            "message": f"Rumor verified successfully by {profile.managed_club.name}!"
        })

    messages.success(request, f"Rumor successfully verified by {profile.managed_club.name} admin.")
    return redirect('rumors:show_rumors_detail', id=id)



# ========== DENY RUMOR ==========
@login_required(login_url='accounts:login_page')
def deny_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    profile = getattr(request.user, "profile", None)

    # Pastikan user adalah admin klub asal atau tujuan
    if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "error": "You are not authorized to deny this rumor."
            }, status=403)
        messages.error(request, "You are not authorized to deny this rumor.")
        return redirect('rumors:show_rumors_detail', id=id)

    # Update status ke denied
    rumor.status = "denied"
    rumor.save()

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "status": rumor.status,
            "message": f"Rumor denied by {profile.managed_club.name} admin."
        })

    # Non-AJAX 
    messages.warning(request, f"Rumor has been denied by {profile.managed_club.name} admin.")
    return redirect('rumors:show_rumors_detail', id=id)


## ========== REVERT RUMOR ==========
@login_required(login_url='accounts:login_page')
def revert_rumor(request, id):
    rumor = get_object_or_404(Rumors, pk=id)
    profile = getattr(request.user, "profile", None)

    # Pastikan user adalah admin klub asal atau tujuan
    if not (request.user.is_club_admin and profile and profile.managed_club in [rumor.club_asal, rumor.club_tujuan]):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "error": "You are not authorized to revert this rumor."
            }, status=403)
        messages.error(request, "You are not authorized to revert this rumor.")
        return redirect('rumors:show_rumors_detail', id=id)

    # Ubah status jadi pending
    rumor.status = "pending"
    rumor.save()

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "status": rumor.status,
            "message": f"Rumor reverted to pending by {profile.managed_club.name} admin."
        })

    # Non-AJAX (fallback)
    messages.info(request, f"Rumor reverted to pending by {profile.managed_club.name} admin.")
    return redirect('rumors:show_rumors_detail', id=id)
