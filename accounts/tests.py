from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Club
from .models import Profile
from .views import _is_superuser_check
# Impor semua form untuk diuji secara langsung
from .forms import (
    UserUpdateForm,
    ProfileUpdateForm,
    SuperUserEditForm,
    SuperUserCreateForm,
    PasswordChangeCustomForm,
)

# Dapatkan model CustomUser yang sedang aktif
CustomUser = get_user_model()

class AccountsViewsTests(TestCase):
    """
    Kelas ini menguji semua view di dalam aplikasi accounts.
    """
    def setUp(self):
        """
        Metode setUp dijalankan sebelum SETIAP metode tes.
        Kita siapkan data dummy di sini.
        """
        self.client = Client()

        self.register_url = reverse('accounts:register_page')
        self.login_url = reverse('accounts:login_page')
        self.logout_url = reverse('accounts:logout_user')
        self.homepage_url = reverse('main:homepage')
        self.register_ajax_url = reverse('accounts:register_ajax')
        self.login_ajax_url = reverse('accounts:login_ajax')
        self.dashboard_url = reverse('accounts:superuser_dashboard')
        self.add_user_url = reverse('accounts:add_user')
        self.edit_profile_url = reverse('accounts:edit_profile')
        self.delete_account_url = reverse('accounts:delete_account')
        
        #  Data Dummy 
        self.admin_club = Club.objects.create(name="admin")
        self.regular_club = Club.objects.create(name="Test Club")

        # User fan biasa
        self.test_user = CustomUser.objects.create_user(username='testuser', password='password123')
        Profile.objects.create(user=self.test_user)

        # User lain untuk target aksi
        self.other_user = CustomUser.objects.create_user(username='otheruser', password='password123')
        Profile.objects.create(user=self.other_user)

        # User admin klub biasa (bukan superuser)
        self.club_admin = CustomUser.objects.create_user(username='clubadmin', password='password123', is_club_admin=True)
        Profile.objects.create(user=self.club_admin, managed_club=self.regular_club)

        # User superuser sejati
        self.superuser = CustomUser.objects.create_user(username='superuser', password='password123', is_club_admin=True, is_fan=True)
        Profile.objects.create(user=self.superuser, managed_club=self.admin_club)
        
        # Payloads
        self.register_payload = {'username': 'fanbaru', 'password': 'passwordaman123', 'password2': 'passwordaman123'}
        self.login_payload = {'username': 'testuser', 'password': 'password123'}

    #  TES MODEL & HELPER 

    def test_model_str_methods(self):
        """Tes metode __str__ pada semua model."""
        self.assertEqual(str(self.test_user), 'testuser')
        self.assertEqual(str(self.test_user.profile), 'testuser Profile')

    def test_is_superuser_check_logic(self):
        """Tes logika helper _is_superuser_check secara langsung."""
        self.assertTrue(_is_superuser_check(self.superuser))
        self.assertFalse(_is_superuser_check(self.club_admin))
        self.assertFalse(_is_superuser_check(self.test_user))

    #  TES VIEW REGISTER, LOGIN, LOGOUT (Dasar) 

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
    def test_authenticated_user_redirected_from_register_page(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.homepage_url)

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_authenticated_user_redirected_from_login_page(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.homepage_url)

    def test_register_ajax_success_and_profile_creation(self):
        response = self.client.post(self.register_ajax_url, self.register_payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'success')
        new_user = CustomUser.objects.get(username='fanbaru')
        self.assertTrue(Profile.objects.filter(user=new_user).exists())

    def test_register_ajax_password_mismatch(self):
        payload = {'username': 'testuser123', 'password': 'password123', 'password2': 'password456'}
        response = self.client.post(self.register_ajax_url, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Password tidak cocok', response.json()['message'])
    
    def test_login_ajax_success_superuser_check(self):
        self.client.login(username='superuser', password='password123')
        response = self.client.post(self.login_ajax_url, {'username': 'superuser', 'password': 'password123'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_superuser'])

    def test_logout_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.homepage_url)
        self.assertFalse('_auth_user_id' in self.client.session)

    #  TES DASHBOARD & AKSI SUPERUSER 

    def test_superuser_dashboard_access_granted(self):
        self.client.login(username='superuser', password='password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertIn('all_users', response.context)

    def test_dashboard_access_denied_for_non_superusers(self):
        # Tes fan biasa
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)
        # Tes admin klub biasa
        self.client.login(username='clubadmin', password='password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_add_user_view_get(self):
        self.client.login(username='superuser', password='password123')
        response = self.client.get(self.add_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SuperUserCreateForm)
    
    def test_add_user_view_post_fail_duplicate_username(self):
        self.client.login(username='superuser', password='password123')
        response = self.client.post(self.add_user_url, {
            'username': 'testuser', 'password': 'password123', 'password2': 'password123', 'role': 'fan'
        })
        self.assertEqual(response.status_code, 200) # Gagal, render ulang halaman
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Terjadi kesalahan. Mohon periksa kembali isian Anda.")

    def test_edit_user_view_post_fail_invalid_data(self):
        self.client.login(username='superuser', password='password123')
        edit_url = reverse('accounts:edit_user', kwargs={'pk': self.other_user.pk})
        response = self.client.post(edit_url, {'username': ''}) # Username kosong
        self.assertEqual(response.status_code, 200) # Gagal, render ulang halaman
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_edit_user_view_get_404(self):
        self.client.login(username='superuser', password='password123')
        edit_url = reverse('accounts:edit_user', kwargs={'pk': 999}) # User tidak ada
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404)

    #  TES EDIT PROFIL PENGGUNA 

    def test_edit_profile_access_denied_for_anonymous(self):
        response = self.client.get(self.edit_profile_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.edit_profile_url}')
    
    def test_edit_profile_username_update_fail_taken(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.edit_profile_url, {
            'username': 'otheruser', # Username sudah dipakai
            'update_username': 'Update Username'
        })
        self.assertEqual(response.status_code, 200) # Render ulang
        self.assertContains(response, 'Gagal memperbarui username.')
        
    def test_edit_profile_password_change_fail_wrong_old_pass(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.edit_profile_url, {
            'old_password': 'passwordsalah',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
            'change_password': 'Change Password'
        })
        self.assertEqual(response.status_code, 200) # Render ulang
        self.assertContains(response, 'Gagal mengubah password.')
        self.assertIn('old_password', response.context['password_form'].errors)
    
    def test_edit_profile_password_change_fail_mismatch(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.edit_profile_url, {
            'old_password': 'password123',
            'new_password1': 'newpass123',
            'new_password2': 'newpassBEDA',
            'change_password': 'Change Password'
        })
        self.assertEqual(response.status_code, 200) # Render ulang
        self.assertContains(response, 'Gagal mengubah password.')
        self.assertIn('new_password2', response.context['password_form'].errors)

    #  TES PENGHAPUSAN AKUN 

    def test_delete_user_access_denied_for_fan(self):
        self.client.login(username='testuser', password='password123')
        delete_url = reverse('accounts:delete_user', kwargs={'pk': self.other_user.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)