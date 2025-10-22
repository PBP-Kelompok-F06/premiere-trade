from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

# Create your views here.
from .models import CustomUser


def login_page(request):
    """
    Menampilkan halaman login.
    Jika user sudah login, redirect ke homepage.
    """
    if request.user.is_authenticated:
        return redirect("main:homepage")
    return render(request, "login.html")


def register_page(request):
    """
    Menampilkan halaman register.
    Jika user sudah login, redirect ke homepage.
    """
    if request.user.is_authenticated:
        return redirect("main:homepage")
    return render(request, "register.html")


@require_POST
def register_ajax(request):
    """
    Menangani registrasi Fan Account via AJAX.
    (Logika internal tidak berubah)
    """
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

        # Buat user baru (is_fan default True)
        user = CustomUser.objects.create_user(username=username, password=password)

        # Langsung login-kan user
        login(request, user)

        return JsonResponse(
            {
                "status": "success",
                "message": "Registrasi berhasil! Anda akan dialihkan...",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}, status=500
        )


@require_POST
def login_ajax(request):
    """
    Menangani login via AJAX.
    (Logika internal tidak berubah)
    """
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
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Login berhasil! Anda akan dialihkan...",
                }
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Username atau password salah."},
                status=400,
            )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}, status=500
        )


def logout_user(request):
    """
    Menangani logout.
    """
    logout(request)
    # Redirect kembali ke homepage
    return redirect("main:homepage")
