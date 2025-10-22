from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Club  # Kita butuh ini untuk membuat Profile
from .models import Profile

# Create your tests here.

# Dapatkan model CustomUser yang sedang aktif
CustomUser = get_user_model()

class AccountsTests(TestCase):

    def setUp(self):
        """
        Metode setUp dijalankan sebelum SETIAP metode tes.
        Kita siapkan data dummy di sini.
        """
        # Buat instance Client untuk simulasi request HTTP
        self.client = Client()

        # Siapkan URL yang akan dites
        self.register_url = reverse('accounts:register_page')
        self.login_url = reverse('accounts:login_page')
        self.logout_url = reverse('accounts:logout_user')
        self.homepage_url = reverse('main:homepage')

        # --- URL BARU UNTUK ENDPOINT AJAX ---
        self.register_ajax_url = reverse('accounts:register_ajax') # BARU
        self.login_ajax_url = reverse('accounts:login_ajax')     # BARU

        # Buat data dummy untuk klub (dibutuhkan oleh Profile)
        self.club = Club.objects.create(name="Test Club")

        # Buat user dummy untuk tes login dan tes "username sudah ada"
        self.test_user = CustomUser.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        # Buat data yang akan dikirim (payload) untuk tes
        self.register_payload = {
            'username': 'fanbaru',
            'password': 'passwordaman123',
            'password2': 'passwordaman123', # DIUBAH: Tambahkan password2 agar validasi di view lolos
        }
        
        self.login_payload = {
            'username': 'testuser',
            'password': 'password123',
        }

    # --- TES MODEL ---

    def test_custom_user_model(self):
        """Tes apakah CustomUser dibuat dengan properti yang benar."""
        user = CustomUser.objects.get(username='testuser')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_fan)
        self.assertFalse(user.is_club_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    # --- TES VIEW REGISTER ---

    def test_register_page_loads(self):
        """Tes apakah halaman register (GET request) bisa dimuat."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html') # DIUBAH: Path disesuaikan

    def test_register_success_ajax(self):
        """Tes registrasi sukses via AJAX (POST request)."""
        response = self.client.post(
            self.register_ajax_url, # DIUBAH: Gunakan URL AJAX
            self.register_payload,
            content_type='application/json', # DIUBAH: Set content_type
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'success')
        self.assertIn('Registrasi berhasil', response.json()['message'])

        self.assertTrue(CustomUser.objects.filter(username='fanbaru').exists())

    def test_register_username_taken_ajax(self):
        """Tes registrasi gagal (username sudah ada) via AJAX."""
        payload = {
            'username': 'testuser',
            'password': 'password123',
            'password2': 'password123',
        }
        response = self.client.post(
            self.register_ajax_url, # DIUBAH: Gunakan URL AJAX
            payload,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertIn('Username sudah digunakan', response.json()['message'])

    # --- TES VIEW LOGIN ---

    def test_login_page_loads(self):
        """Tes apakah halaman login (GET request) bisa dimuat."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html') # DIUBAH: Path disesuaikan

    def test_login_success_ajax(self):
        """Tes login sukses via AJAX (POST request)."""
        response = self.client.post(
            self.login_ajax_url, # DIUBAH: Gunakan URL AJAX
            self.login_payload,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertIn('Login berhasil', response.json()['message'])
        
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.test_user.pk))

    def test_login_wrong_password_ajax(self):
        """Tes login gagal (password salah) via AJAX."""
        payload = {
            'username': 'testuser',
            'password': 'passwordSALAH',
        }
        response = self.client.post(
            self.login_ajax_url, # DIUBAH: Gunakan URL AJAX
            payload,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['status'], 'error')
        self.assertIn('Username atau password salah', response.json()['message'])
        
        self.assertFalse('_auth_user_id' in self.client.session)

    # --- TES VIEW LOGOUT ---
    
    def test_logout_view(self):
        """Tes logout view (GET request)."""
        self.client.login(username='testuser', password='password123')
        self.assertTrue('_auth_user_id' in self.client.session)

        response = self.client.get(self.logout_url)
        
        self.assertRedirects(response, self.homepage_url)
        self.assertFalse('_auth_user_id' in self.client.session)