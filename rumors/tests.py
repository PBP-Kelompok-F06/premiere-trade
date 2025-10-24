from django.test import TestCase, Client
from django.urls import reverse
from rumors.models import Rumors
from main.models import Club, Player
from accounts.models import CustomUser, Profile


class RumorsTest(TestCase):
    def setUp(self):
        #Clear semua data sebelum tiap test
        Club.objects.all().delete()
        Player.objects.all().delete()
        Rumors.objects.all().delete()
        CustomUser.objects.all().delete()
        Profile.objects.all().delete()
        # Setup data untuk semua test
        self.client = Client()

        # Buat user biasa dan admin club
        self.fan_user = CustomUser.objects.create_user(username="fanuser", password="password123", is_fan=True)
        self.admin_user = CustomUser.objects.create_user(username="clubadmin", password="password123", is_club_admin=True)

        # Buat club dan assign ke admin
        self.club_a = Club.objects.create(name="Chelsea", country="England")
        self.club_b = Club.objects.create(name="Arsenal", country="England")
        Profile.objects.create(user=self.admin_user, managed_club=self.club_a)

        # Buat pemain
        self.player = Player.objects.create(
            current_club=self.club_a,
            nama_pemain="Enzo Fernandez",
            position="Midfielder",
            umur=23,
            market_value=100000000,
            negara="Argentina",
        )

        # Buat rumor awal
        self.rumor = Rumors.objects.create(
            author=self.fan_user,
            pemain=self.player,
            club_asal=self.club_a,
            club_tujuan=self.club_b,
            content="Enzo Fernandez transfer to Arsenal is heating up."
        )

    # ========== MODEL TESTS ==========
    def test_rumor_title_auto_generated(self):
        self.assertEqual(
            self.rumor.title,
            f"{self.player.nama_pemain} transfer from {self.club_a.name} to {self.club_b.name}"
        )

    def test_increment_views(self):
        initial_views = self.rumor.rumors_views
        self.rumor.increment_views()
        self.assertEqual(self.rumor.rumors_views, initial_views + 1)

    # ========== VIEW TESTS ==========
    def test_show_rumors_main_url_exists(self):
        response = self.client.get(reverse('rumors:show_rumors_main'))
        self.assertEqual(response.status_code, 200)

    def test_show_rumors_detail_url_exists(self):
        response = self.client.get(reverse('rumors:show_rumors_detail', args=[self.rumor.id]))
        self.assertEqual(response.status_code, 200)

    def test_create_rumor_as_fan_success(self):
        self.client.login(username="fanuser", password="password123")
        response = self.client.post(reverse('rumors:create_rumors'), {
            'club_asal': self.club_a.id,
            'club_tujuan': self.club_b.id,
            'pemain': self.player.id,
            'content': 'Testing rumor creation'
        })
        self.assertEqual(response.status_code, 302)  # Redirect sukses

    def test_create_rumor_as_admin_forbidden(self):
        self.client.login(username="clubadmin", password="password123")
        response = self.client.post(reverse('rumors:create_rumors'), {
            'club_asal': self.club_a.id,
            'club_tujuan': self.club_b.id,
            'pemain': self.player.id,
            'content': 'Should not be allowed'
        })
        self.assertEqual(response.status_code, 302)  # Redirect karena tidak boleh
        self.assertEqual(Rumors.objects.count(), 1)  # Tidak bertambah

    def test_edit_rumor_resets_status_when_verified(self):
        # Ubah status ke verified
        self.rumor.status = "verified"
        self.rumor.save()

        self.client.login(username="fanuser", password="password123")
        response = self.client.post(reverse('rumors:edit_rumors', args=[self.rumor.id]), {
            'club_asal': self.club_a.id,
            'club_tujuan': self.club_b.id,
            'pemain': self.player.id,
            'content': 'Rumor updated'
        })
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.status, "pending")  # Reset ke pending

    def test_edit_rumor_no_change_does_not_reset_status(self):
        self.rumor.status = "verified"
        self.rumor.save()

        self.client.login(username="fanuser", password="password123")
        response = self.client.post(reverse('rumors:edit_rumors', args=[self.rumor.id]), {
            'club_asal': self.club_a.id,
            'club_tujuan': self.club_b.id,
            'pemain': self.player.id,
            'content': self.rumor.content  # Tidak ada perubahan
        })
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.status, "verified")  # Tetap verified

    def test_delete_rumor_by_author_success(self):
        self.client.login(username="fanuser", password="password123")
        response = self.client.post(reverse('rumors:delete_rumors', args=[self.rumor.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Rumors.objects.filter(id=self.rumor.id).exists())

    def test_delete_rumor_by_other_user_forbidden(self):
        another_user = CustomUser.objects.create_user(username="otheruser", password="password123")
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(reverse('rumors:delete_rumors', args=[self.rumor.id]))
        self.assertEqual(response.status_code, 403)

    def test_verify_rumor_by_author_forbidden(self):
        self.client.login(username="fanuser", password="password123")
        response = self.client.get(reverse('rumors:verify_rumor', args=[self.rumor.id]))
        self.assertEqual(response.status_code, 302)
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.status, "pending")

    def test_verify_rumor_by_admin_success(self):
        self.client.login(username="clubadmin", password="password123")
        response = self.client.get(reverse('rumors:verify_rumor', args=[self.rumor.id]))
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.status, "verified")
