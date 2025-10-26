from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import (
    UserUpdateForm,
    SuperUserEditForm,
    SuperUserCreateForm,
    PasswordChangeCustomForm,
    ClubForm,
    PlayerForm,
)
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from main.models import Club, Player
from django.shortcuts import get_object_or_404
from .models import CustomUser, Profile
import json

# Create your views here.


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("main:homepage")
    return render(request, "login.html")


@ensure_csrf_cookie
def register_page(request):
    if request.user.is_authenticated:
        return redirect("main:homepage")
    return render(request, "register.html")


@require_POST
def register_ajax(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        password2 = data.get("password2")

        if not (username and password and password2):
            return JsonResponse(
                {"status": "error", "message": "Semua field harus diisi."}, status=400
            )
        if password != password2:
            return JsonResponse(
                {"status": "error", "message": "Password tidak cocok."}, status=400
            )
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse(
                {"status": "error", "message": "Username sudah digunakan."}, status=400
            )

        user = CustomUser.objects.create_user(username=username, password=password)
        # Otomatis buat profile saat user register
        Profile.objects.create(user=user)

        login(request, user)

        return JsonResponse(
            {
                "status": "success",
                "message": "Registrasi berhasil! Anda akan dialihkan...",
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}, status=500
        )


@require_POST
def login_ajax(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        if not (username and password):
            return JsonResponse(
                {"status": "error", "message": "Username dan password harus diisi."},
                status=400,
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Cek apakah user adalah superuser
            is_superuser = _is_superuser_check(user)

            # Siapkan data JSON untuk dikirim kembali
            response_data = {
                "status": "success",
                "message": "Login berhasil! Anda akan dialihkan...",
                "is_superuser": is_superuser,  # Kirim status superuser
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse(
                {"status": "error", "message": "Username atau password salah."},
                status=401,
            )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}, status=500
        )


def logout_user(request):
    logout(request)
    return redirect("main:homepage")


def _is_superuser_check(user):
    """Fungsi helper untuk memeriksa hak akses superuser."""
    return (
        user.is_authenticated
        and user.is_fan
        and user.is_club_admin
        and hasattr(user, "profile")
        and user.profile.managed_club is not None
        and user.profile.managed_club.name.lower() == "admin"
    )


@login_required
def superuser_dashboard(request):
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    # Pengambilan Data untuk Dashboard
    all_users = CustomUser.objects.all().order_by("username")
    all_clubs = Club.objects.all().order_by("name")
    all_players = Player.objects.all().order_by("nama_pemain")  # Tambahkan ini

    # Hitung jumlah untuk ditampilkan di card
    user_count = all_users.exclude(is_superuser=True).count()
    club_count = all_clubs.count()
    player_count = all_players.count()

    context = {
        "all_users": all_users,
        "all_clubs": all_clubs,
        "all_players": all_players,
        "user_count": user_count - 1,
        "club_count": club_count - 1,
        "player_count": player_count,
    }

    return render(request, "dashboard.html", context)


@login_required
def edit_user(request, pk):
    # Pastikan hanya superuser yang bisa mengakses halaman ini
    if not _is_superuser_check(request.user):
        raise PermissionDenied(
            "Anda tidak memiliki akses untuk melakukan tindakan ini."
        )

    # Dapatkan user yang akan diedit, atau 404 jika tidak ada
    user_to_edit = get_object_or_404(CustomUser, pk=pk)

    if request.method == "POST":
        form = SuperUserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Profil '{user_to_edit.username}' berhasil diperbarui."
            )
            return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        # Tampilkan form dengan data user yang ada
        form = SuperUserEditForm(instance=user_to_edit)

    context = {"form": form, "user_to_edit": user_to_edit}
    return render(request, "edit_user.html", context)


@login_required
def add_user(request):
    # Pastikan hanya superuser yang bisa mengakses
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    if request.method == "POST":
        form = SuperUserCreateForm(request.POST)
        if form.is_valid():
            # Cek duplikasi username secara manual karena create_user bisa error
            if CustomUser.objects.filter(
                username=form.cleaned_data["username"]
            ).exists():
                messages.error(request, "Username sudah digunakan.")
            else:
                form.save()
                messages.success(
                    request,
                    f"Pengguna '{form.cleaned_data['username']}' berhasil dibuat.",
                )
                return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        form = SuperUserCreateForm()

    context = {"form": form}
    return render(request, "add_user.html", context)


@login_required
def edit_profile(request):
    # Logika untuk form ganti password
    if "change_password" in request.POST:
        password_form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password Anda berhasil diubah.")
            return redirect("accounts:edit_profile")
        else:
            messages.error(
                request, "Gagal mengubah password. Silakan periksa error di bawah."
            )
            user_form = UserUpdateForm(instance=request.user)

    # Logika untuk form update username
    elif "update_username" in request.POST:
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Username Anda berhasil diperbarui.")
            return redirect("accounts:edit_profile")
        else:
            messages.error(request, "Gagal memperbarui username.")
            password_form = PasswordChangeCustomForm(user=request.user)

    # Jika method GET (pertama kali buka halaman)
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeCustomForm(user=request.user)

    context = {
        "user_form": user_form,
        "password_form": password_form,
    }
    return render(request, "edit_profile.html", context)


@login_required
@require_POST
def delete_account(request):
    user = request.user
    # Lakukan logout sebelum menghapus untuk membersihkan session
    logout(request)
    # Hapus user dari database
    user.delete()
    messages.success(request, "Akun Anda telah berhasil dihapus secara permanen.")
    # Redirect ke halaman utama atau halaman login
    return redirect("main:homepage")


@login_required
@require_POST
def delete_user(request, pk):
    # Pastikan hanya superuser yang bisa mengakses
    if not _is_superuser_check(request.user):
        raise PermissionDenied(
            "Anda tidak memiliki akses untuk melakukan tindakan ini."
        )

    # Ambil user yang akan dihapus
    user_to_delete = get_object_or_404(CustomUser, pk=pk)

    # Pastikan superuser tidak bisa menghapus akunnya sendiri dari sini
    if user_to_delete == request.user:
        messages.error(
            request, "Anda tidak dapat menghapus akun Anda sendiri dari dashboard."
        )
        return redirect("accounts:superuser_dashboard")

    username = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f"Pengguna '{username}' telah berhasil dihapus.")
    return redirect("accounts:superuser_dashboard")


@ensure_csrf_cookie
def register_page(request):
    if request.user.is_authenticated:
        return redirect("main:homepage")
    return render(request, "register.html")


@login_required
def add_club(request):
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    if request.method == "POST":
        form = ClubForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Klub '{form.cleaned_data['name']}' berhasil ditambahkan."
            )
            return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        form = ClubForm()

    context = {"form": form, "title": "Tambah Klub Baru"}
    return render(request, "club_form.html", context)


@login_required
def edit_club(request, pk):
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    club_to_edit = get_object_or_404(Club, pk=pk)

    if request.method == "POST":
        form = ClubForm(request.POST, instance=club_to_edit)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Klub '{club_to_edit.name}' berhasil diperbarui."
            )
            return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        form = ClubForm(instance=club_to_edit)

    context = {
        "form": form,
        "club_to_edit": club_to_edit,
        "title": f"Edit Klub: {club_to_edit.name}",
    }
    return render(request, "club_form.html", context)


@login_required
@require_POST
def delete_club(request, pk):
    if not _is_superuser_check(request.user):
        raise PermissionDenied(
            "Anda tidak memiliki akses untuk melakukan tindakan ini."
        )

    club_to_delete = get_object_or_404(Club, pk=pk)

    club_name = club_to_delete.name
    club_to_delete.delete()
    messages.success(
        request, f"Klub '{club_name}' dan semua pemain terkait berhasil dihapus."
    )
    return redirect("accounts:superuser_dashboard")


@login_required
def add_player(request):
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    if request.method == "POST":
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Pemain '{form.cleaned_data['nama_pemain']}' berhasil ditambahkan.",
            )
            return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        form = PlayerForm()

    context = {"form": form, "title": "Tambah Pemain Baru"}
    return render(request, "player_form.html", context)


@login_required
def edit_player(request, pk):
    if not _is_superuser_check(request.user):
        raise PermissionDenied("Anda tidak memiliki akses ke halaman ini.")

    player_to_edit = get_object_or_404(Player, pk=pk)

    if request.method == "POST":
        form = PlayerForm(request.POST, instance=player_to_edit)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Pemain '{player_to_edit.nama_pemain}' berhasil diperbarui."
            )
            return redirect("accounts:superuser_dashboard")
        else:
            messages.error(
                request, "Terjadi kesalahan. Mohon periksa kembali isian Anda."
            )
    else:
        form = PlayerForm(instance=player_to_edit)

    context = {
        "form": form,
        "player_to_edit": player_to_edit,
        "title": f"Edit Pemain: {player_to_edit.nama_pemain}",
    }
    return render(request, "player_form.html", context)


@login_required
@require_POST
def delete_player(request, pk):
    if not _is_superuser_check(request.user):
        raise PermissionDenied(
            "Anda tidak memiliki akses untuk melakukan tindakan ini."
        )

    player_to_delete = get_object_or_404(Player, pk=pk)

    player_name = player_to_delete.nama_pemain
    player_to_delete.delete()
    messages.success(request, f"Pemain '{player_name}' berhasil dihapus.")
    return redirect("accounts:superuser_dashboard")


