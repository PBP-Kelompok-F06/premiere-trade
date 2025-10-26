from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Player, Club
from accounts.models import Profile
from player_transaction.models import Negotiation
import json

User = get_user_model()


class PlayerTransactionViewTests(TestCase):
    def setUp(self):
        Club.objects.all().delete()
        Profile.objects.all().delete()
        Player.objects.all().delete()
        Negotiation.objects.all().delete()
        User = get_user_model()
        User.objects.all().delete()

        # Client untuk simulasi HTTP request
        self.client = Client()


        # --- Buat user & profil club admin ---
        self.club_a, _ = Club.objects.get_or_create(name="Arsenal", defaults={"country": "England"})
        self.club_b, _ = Club.objects.get_or_create(name="Chelsea", defaults={"country": "England"})

        self.user_a = User.objects.create_user(username="arsenal_admin", password="12345", is_club_admin=True)
        self.user_b = User.objects.create_user(username="chelsea_admin", password="12345", is_club_admin=True)

        self.profile_a = Profile.objects.create(user=self.user_a, managed_club=self.club_a)
        self.profile_b = Profile.objects.create(user=self.user_b, managed_club=self.club_b)

        # --- Buat pemain-pemain ---
        self.player_a = Player.objects.create(
            nama_pemain="Bukayo Saka",
            current_club=self.club_a,
            position="RW",
            umur=22,
            negara="England",
            market_value=80000000,
            sedang_dijual=False,
        )

        self.player_b = Player.objects.create(
            nama_pemain="Enzo Fernandez",
            current_club=self.club_b,
            position="CM",
            umur=23,
            negara="Argentina",
            market_value=70000000,
            sedang_dijual=True,
        )

    def login_as(self, user):
        self.client.login(username=user.username, password="12345")

    def test_list_pemain_saya_returns_hanya_pemain_klub_login(self):
        self.login_as(self.user_a)
        response = self.client.get(reverse("player_transaction:list_pemain_saya"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nama_pemain"], "Bukayo Saka")

    def test_jual_pemain_ajax_berhasil(self):
        """Klub bisa menjual pemain miliknya"""
        self.login_as(self.user_a)
        url = reverse("player_transaction:jual_pemain_ajax", args=[self.player_a.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.player_a.refresh_from_db()
        self.assertTrue(self.player_a.sedang_dijual)

    def test_batalkan_jual_pemain_ajax_berhasil(self):
        self.login_as(self.user_b)
        url = reverse("player_transaction:batalkan_jual_pemain_ajax", args=[self.player_b.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.player_b.refresh_from_db()
        self.assertFalse(self.player_b.sedang_dijual)

    def test_beli_pemain_ajax_berhasil(self):
        """Klub A bisa membeli pemain dari klub B"""
        self.login_as(self.user_a)
        url = reverse("player_transaction:beli_pemain_ajax", args=[self.player_b.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.player_b.refresh_from_db()
        self.assertEqual(self.player_b.current_club, self.club_a)

    def test_beli_pemain_gagal_jika_klub_sama(self):
        self.login_as(self.user_a)
        url = reverse("player_transaction:beli_pemain_ajax", args=[self.player_a.id])
        response = self.client.post(url)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Tidak bisa membeli pemain klub sendiri", data["message"])


    def test_send_negotiation_berhasil(self):
        """Klub A kirim tawaran ke pemain dari klub B"""
        self.login_as(self.user_a)
        url = reverse("player_transaction:send_negotiation", args=[self.player_b.id])
        response = self.client.post(
            url,
            data=json.dumps({"offered_price": 60000000}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(Negotiation.objects.exists())

    def test_send_negotiation_gagal_ke_pemain_sendiri(self):
        self.login_as(self.user_a)
        url = reverse("player_transaction:send_negotiation", args=[self.player_a.id])
        response = self.client.post(
            url,
            data=json.dumps({"offered_price": 10000000}),
            content_type="application/json",
        )
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Tidak bisa menawar pemain dari klub sendiri", data["message"])

    def test_respond_negotiation_accept_berhasil(self):
        """Klub penerima tawaran bisa menerima"""
        nego = Negotiation.objects.create(
            from_club=self.club_a,
            to_club=self.club_b,
            player=self.player_b,
            offered_price=50000000,
        )
        self.login_as(self.user_b)
        url = reverse("player_transaction:respond_negotiation", args=[nego.id, "accept"])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        nego.refresh_from_db()
        self.assertEqual(nego.status, "accepted")
        self.player_b.refresh_from_db()
        self.assertEqual(self.player_b.current_club, self.club_a)

    def test_respond_negotiation_reject_berhasil(self):
        nego = Negotiation.objects.create(
            from_club=self.club_a,
            to_club=self.club_b,
            player=self.player_b,
            offered_price=50000000,
        )
        self.login_as(self.user_b)
        url = reverse("player_transaction:respond_negotiation", args=[nego.id, "reject"])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        nego.refresh_from_db()
        self.assertEqual(nego.status, "rejected")

    def test_negotiation_inbox_json(self):
        nego = Negotiation.objects.create(
            from_club=self.club_a,
            to_club=self.club_b,
            player=self.player_b,
            offered_price=40000000,
        )
        self.login_as(self.user_b)
        response = self.client.get(reverse("player_transaction:negotiation_inbox_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("received_offers", data)
        self.assertGreaterEqual(len(data["received_offers"]), 1)
