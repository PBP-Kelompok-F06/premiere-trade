from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json

User = get_user_model()


# Create your views here.
@csrf_exempt
def login(request):
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            # Login status successful.
            return JsonResponse(
                {
                    "username": user.username,
                    "status": True,
                    "message": "Login successful!",
                    # Add other data if you want to send data to Flutter.
                },
                status=200,
            )
        else:
            return JsonResponse(
                {"status": False, "message": "Login failed, account is disabled."},
                status=401,
            )

    else:
        return JsonResponse(
            {
                "status": False,
                "message": "Login failed, please check your username or password.",
            },
            status=401,
        )


@csrf_exempt
def register(request):
    if request.method == "POST":
        # 1. MENCOBA MEMBACA DATA (Support JSON & Form Data)
        try:
            # Coba baca sebagai JSON
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Jika gagal, berarti dikirim sebagai Form Data (default pbp_django_auth)
            data = request.POST

        # 2. AMBIL DATA DENGAN KEY YANG BENAR
        # Gunakan .get() agar tidak error 500 jika key tidak ada
        username = data.get("username")
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        # 3. VALIDASI INPUT
        if not username or not password or not password_confirm:
            return JsonResponse(
                {"status": False, "message": "Semua field harus diisi."}, 
                status=400
            )

        if password != password_confirm:
            return JsonResponse(
                {"status": False, "message": "Password tidak cocok."}, 
                status=400
            )

        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"status": False, "message": "Username sudah digunakan."}, 
                status=400
            )

        # 4. BUAT USER
        user = User.objects.create_user(username=username, password=password)
        user.save()

        return JsonResponse(
            {
                "status": True,
                "message": "Akun berhasil dibuat!",
                "username": user.username,
            },
            status=200,
        )

    return JsonResponse(
        {"status": False, "message": "Invalid request method."}, 
        status=405
    )


@csrf_exempt
def logout(request):
    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse(
            {
                "username": username,
                "status": True,
                "message": "Logged out successfully!",
            },
            status=200,
        )
    except:
        return JsonResponse({"status": False, "message": "Logout failed."}, status=401)
