from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Club
from .models import Profile
from .views import _is_superuser_check # Impor fungsi helper

# Dapatkan model CustomUser yang sedang aktif
CustomUser = get_user_model()

class AccountsTests(TestCase):

    def setUp(self):
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
        
        # Data Dummy
        self.admin_club = Club.objects.create(name="admin")
        self.regular_club = Club.objects.create(name="Test Club")

        # User fan biasa
        self.test_user = CustomUser.objects.create_user(username='testuser', password='password123')
        Profile.objects.create(user=self.test_user)

        # User untuk dihapus
        self.user_to_delete = CustomUser.objects.create_user(username='delete_me', password='password123')
        Profile.objects.create(user=self.user_to_delete)

        # User admin klub biasa (bukan superuser)
        self.club_admin = CustomUser.objects.create_user(username='clubadmin', password='password123', is_club_admin=True)
        Profile.objects.create(user=self.club_admin, managed_club=self.regular_club)

        # User superuser sejati
        self.superuser = CustomUser.objects.create_user(username='superuser', password='password123', is_club_admin=True, is_fan=True)
        # Profile untuk superuser harus dibuat dan dihubungkan ke klub 'admin'
        Profile.objects.create(user=self.superuser, managed_club=self.admin_club)
        
        # Payloads
        self.register_payload = {'username': 'fanbaru', 'password': 'passwordaman123', 'password2': 'passwordaman123'}
        self.login_payload = {'username': 'testuser', 'password': 'password123'}

    # TES MODEL & HELPER

    def test_custom_user_model(self):
        """Tes apakah CustomUser dibuat dengan properti yang benar."""
        user = CustomUser.objects.get(username='testuser')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_fan)
        self.assertFalse(user.is_club_admin)

    def test_is_superuser_check_logic(self):
        """Tes logika helper _is_superuser_check secara langsung."""
        self.assertTrue(_is_superuser_check(self.superuser))
        self.assertFalse(_is_superuser_check(self.club_admin))
        self.assertFalse(_is_superuser_check(self.test_user))

    # TES VIEW REGISTER & LOGIN

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_success_ajax(self):
        response = self.client.post(self.register_ajax_url, self.register_payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(CustomUser.objects.filter(username='fanbaru').exists())

    def test_register_username_taken_ajax(self):
        payload = {'username': 'testuser', 'password': 'password123', 'password2': 'password123'}
        response = self.client.post(self.register_ajax_url, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_success_ajax(self):
        response = self.client.post(self.login_ajax_url, self.login_payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_wrong_password_ajax(self):
        payload = {'username': 'testuser', 'password': 'passwordSALAH'}
        response = self.client.post(self.login_ajax_url, payload, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['status'], 'error')

    # TES VIEW LOGOUT
    
    def test_logout_view(self):
        self.client.login(username='testuser', password='password123')
        self.assertTrue('_auth_user_id' in self.client.session)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.homepage_url)
        self.assertFalse('_auth_user_id' in self.client.session)

    # TES DASHBOARD SUPERUSER

    def test_superuser_dashboard_access_granted(self):
        """Tes superuser bisa mengakses dashboard."""
        self.client.login(username='superuser', password='password123')
        response = self.client.get(self.dashboard_url)