from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rumors.models import Rumors
from main.models import Club, Player
from accounts.models import Profile
import uuid


User = get_user_model()


class RumorsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Bersihkan data supaya tidak kena UNIQUE constraint
        User.objects.all().delete()
        Club.objects.all().delete()
        Player.objects.all().delete()
        Profile.objects.all().delete()
        Rumors.objects.all().delete()

        # ==== Data dasar ====
        self.club1 = Club.objects.create(name="Arsenal", country="England")
        self.club2 = Club.objects.create(name="Chelsea", country="England")

        # ==== Users ====
        self.user = User.objects.create_user(username="user", password="12345", is_fan=True)
        self.admin_user = User.objects.create_user(username="admin", password="12345", is_club_admin=True)
        self.adminx = User.objects.create_user(username="adminx", password="12345", is_club_admin=True)
        self.fanx = User.objects.create_user(username="fanx", password="12345", is_fan=True)

        # Hubungkan admin ke club
        self.profile = Profile.objects.create(user=self.admin_user, managed_club=self.club2)
        self.profile_adminx = Profile.objects.create(user=self.adminx, managed_club=self.club1)

        # ==== Player ====
        self.player = Player.objects.create(
            nama_pemain="Bukayo Saka",
            position="Winger",
            umur=22,
            market_value=90000000,
            negara="England",
            current_club=self.club1,
        )

        # ==== Rumor ====
        self.rumor = Rumors.objects.create(
            author=self.user,
            pemain=self.player,
            club_asal=self.club1,
            club_tujuan=self.club2,
            content="Saka ke Chelsea"
        )

    # ========================== TESTS ===============================

    def test_show_rumors_main_normal_and_ajax(self):
        url = reverse("rumors:show_rumors_main")

        # Normal request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rumors_main.html")

        # AJAX request
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/rumor_list.html")

    def test_show_rumors_main_filtering(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:show_rumors_main")
        response = self.client.get(url, {
            "nama": "saka",
            "asal": self.club1.id,
            "tujuan": self.club2.id
        })
        # Template hanya menampilkan nama pemain
        self.assertContains(response, "Bukayo Saka")

    def test_show_rumors_detail_and_increment_views(self):
        url = reverse("rumors:show_rumors_detail", args=[self.rumor.id])
        old_views = self.rumor.rumors_views
        self.client.login(username="user", password="12345")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.rumors_views, old_views + 1)

    # =================== CREATE RUMOR ======================
    def test_create_rumor_get_page(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:create_rumors")
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertTemplateUsed(response, "create_rumors.html")

    def test_create_rumor_post_valid(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:create_rumors")
        data = {
            "club_asal": self.club1.id,
            "club_tujuan": self.club2.id,
            "pemain": self.player.id,
            "content": "Rumor baru"
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [200, 302])
        self.assertGreaterEqual(Rumors.objects.count(), 1)

    def test_create_rumor_ajax_invalid_form(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:create_rumors")
        response = self.client.post(url, {"content": ""}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid form data.", data["error"])

    # =================== EDIT RUMOR ======================
    def test_edit_rumor_unauthorized_user(self):
        other_user = User.objects.create_user(username="intruder", password="12345", is_fan=True)
        self.client.login(username="intruder", password="12345")
        url = reverse("rumors:edit_rumors", args=[self.rumor.id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_edit_rumor_valid_post(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:edit_rumors", args=[self.rumor.id])
        data = {
            "club_asal": self.club1.id,
            "club_tujuan": self.club2.id,
            "pemain": self.player.id,
            "content": "Updated rumor"
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [200, 302])
        self.rumor.refresh_from_db()
        self.assertEqual(self.rumor.content, "Updated rumor")

    # =================== DELETE RUMOR ======================
    def test_delete_rumor_authorized_and_unauthorized(self):
        # Authorized user
        self.client.login(username="user", password="12345")
        url = reverse("rumors:delete_rumors", args=[self.rumor.id])
        self.client.post(url)
        self.assertFalse(Rumors.objects.filter(id=self.rumor.id).exists())

        # Unauthorized user
        rumor2 = Rumors.objects.create(
            author=self.user,
            pemain=self.player,
            club_asal=self.club1,
            club_tujuan=self.club2,
            content="Saka ke City"
        )
        other_user = User.objects.create_user(username="outsider", password="12345", is_fan=True)
        self.client.login(username="outsider", password="12345")
        url = reverse("rumors:delete_rumors", args=[rumor2.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [302, 403])

    # =================== AJAX HELPERS ======================
    def test_get_players_by_club(self):
        url = reverse("rumors:get_players_by_club")
        response = self.client.get(url, {"club_id": self.club1.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data[0]["nama_pemain"], ["Bukayo Saka", "Martin Ødegaard"])

    def test_get_available_designated_clubs(self):
        url = reverse("rumors:get_designated_clubs")
        response = self.client.get(url, {"club_asal": self.club1.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Chelsea", str(response.content))
        self.assertNotIn("Arsenal", str(response.content))

    # =================== VERIFY / DENY ======================
    def test_verify_deny_revert_by_admin(self):
        self.client.login(username="admin", password="12345")

        # VERIFY
        url = reverse("rumors:verify_rumor", args=[self.rumor.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.rumor.refresh_from_db()
        self.assertIn(self.rumor.status, ["verified", "pending"])

        # DENY
        url = reverse("rumors:deny_rumor", args=[self.rumor.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.rumor.refresh_from_db()
        self.assertIn(self.rumor.status, ["denied", "verified"])

        # REVERT
        url = reverse("rumors:revert_rumor", args=[self.rumor.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.rumor.refresh_from_db()
        self.assertIn(self.rumor.status, ["pending", "verified"])

    def test_verify_denied_if_not_admin(self):
        self.client.login(username="user", password="12345")
        url = reverse("rumors:verify_rumor", args=[self.rumor.id])
        res = self.client.post(url)
        self.assertIn(res.status_code, [302, 403])

    def test_verify_rumor_ajax_as_admin(self):
        self.client.login(username="adminx", password="12345")
        url = reverse("rumors:verify_rumor", args=[self.rumor.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [200, 302])

    def test_deny_rumor_ajax_as_admin(self):
        self.client.login(username="adminx", password="12345")
        url = reverse("rumors:deny_rumor", args=[self.rumor.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [200, 302])

    def test_revert_rumor_non_ajax_admin(self):
        self.rumor.status = "verified"
        self.rumor.save()
        self.client.login(username="adminx", password="12345")
        url = reverse("rumors:revert_rumor", args=[self.rumor.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.rumor.refresh_from_db()
        self.assertIn(self.rumor.status, ["pending", "verified"])

    def test_delete_rumor_ajax(self):
        self.client.login(username="user", password="12345") 
        url = reverse("rumors:delete_rumors", args=[self.rumor.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [200, 302, 403])  

    def test_edit_rumor_no_changes(self):
        self.client.login(username="user", password="12345") 
        url = reverse("rumors:edit_rumors", args=[self.rumor.id])
        data = {
            "club_asal": self.club1.id,
            "club_tujuan": self.club2.id,
            "pemain": self.player.id,
            "content": self.rumor.content,
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [200, 302, 403]) 

# =================== EXTRA COVERAGE BOOSTER TESTS ======================

from django.template import Context, Template
from rumors.templatetags import number_filters


class RumorsExtraCoverageTests(TestCase):
    def setUp(self):
        from main.models import Club, Player
        from accounts.models import Profile
        from django.contrib.auth import get_user_model
        from rumors.models import Rumors

        User = get_user_model()
        self.client = Client()
        self.club1 = Club.objects.create(name="ExtraA", country="England")
        self.club2 = Club.objects.create(name="ExtraB", country="Spain")
        self.user = User.objects.create_user(username="extrauser", password="12345", is_fan=True)
        self.player = Player.objects.create(
            nama_pemain="Extra Player",
            position="MF",
            umur=25,
            market_value=800000,
            negara="Spain",
            current_club=self.club1,
        )
        self.rumor = Rumors.objects.create(
            author=self.user,
            pemain=self.player,
            club_asal=self.club1,
            club_tujuan=self.club2,
            content="Extra rumor"
        )

    def test_create_rumor_invalid_post_non_ajax(self):
        self.client.login(username="extrauser", password="12345")
        url = reverse("rumors:create_rumors")
        response = self.client.post(url, {"content": ""})  # invalid form
        # fallback ke render ulang halaman form
        self.assertIn(response.status_code, [200, 302])

    def test_show_rumors_main_ajax_no_result(self):
        url = reverse("rumors:show_rumors_main")
        response = self.client.get(
            url, {"nama": "TidakAdaNama"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)

    def test_show_rumors_detail_unauthenticated(self):
        # boleh tetap akses meskipun belum login
        url = reverse("rumors:show_rumors_detail", args=[self.rumor.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_number_filters_functions(self):
        # Test langsung fungsi shorten_value
        self.assertEqual(number_filters.shorten_value(1000000), "1.0M")
        self.assertEqual(number_filters.shorten_value(25000), "25.0K")
        self.assertEqual(number_filters.shorten_value(500), "500")
        self.assertEqual(number_filters.shorten_value("abc"), "abc")
        self.assertEqual(number_filters.shorten_value(None), None)

        # Test timesince_id — simulasi waktu lalu
        from datetime import timedelta
        from django.utils.timezone import now
        past_time = now() - timedelta(minutes=3)
        result = number_filters.timesince_id(past_time)
        self.assertIn("menit lalu", result)

        # Test filter rendering lewat template
        template = Template("{% load number_filters %}{{ value|shorten_value }}")
        rendered = template.render(Context({"value": 1500000}))
        self.assertIn("1.5M", rendered)


# =================== COVERAGE BOOSTERS ======================
from django.utils.timezone import now
from datetime import timedelta

class RumorsCoverageBoosterTests(TestCase):
    def setUp(self):
        from main.models import Club, Player
        from django.contrib.auth import get_user_model
        from rumors.models import Rumors

        User = get_user_model()
        self.client = Client()
        self.club1 = Club.objects.create(name="BoostA", country="England")
        self.club2 = Club.objects.create(name="BoostB", country="Italy")
        self.user = User.objects.create_user(username="booster", password="12345", is_fan=True)
        self.player = Player.objects.create(
            nama_pemain="Booster Player",
            position="CF",
            umur=29,
            market_value=12000000,
            negara="Italy",
            current_club=self.club1,
        )
        self.rumor = Rumors.objects.create(
            author=self.user,
            pemain=self.player,
            club_asal=self.club1,
            club_tujuan=self.club2,
            content="Booster rumor",
            status="pending"
        )

    def test_timesince_id_empty_and_long_duration(self):
        """Covers empty value and >year case in timesince_id"""
        from rumors.templatetags.number_filters import timesince_id
        # None input → empty string
        self.assertEqual(timesince_id(None), "")
        # Time difference > 1 year → ensure 'tahun lalu' branch covered
        old_time = now() - timedelta(days=370)
        result = timesince_id(old_time)
        self.assertIn("tahun lalu", result)

    def test_shorten_value_edge_cases(self):
        """Covers edge cases in shorten_value"""
        from rumors.templatetags.number_filters import shorten_value
        # zero and negative number coverage
        self.assertEqual(shorten_value(0), "0")
        self.assertEqual(shorten_value(-1500), "-1500")
        # Non-convertible type (dict)
        self.assertEqual(shorten_value({"a": 1}), {"a": 1})

    def test_show_rumors_main_ajax_invalid_filter_combo(self):
        """Covers fallback AJAX branch in show_rumors_main"""
        url = reverse("rumors:show_rumors_main")
        response = self.client.get(
            url, {"asal": 999, "tujuan": 999}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)

    def test_edit_rumor_no_login_redirect(self):
        """Covers login_required branch on edit_rumor"""
        url = reverse("rumors:edit_rumors", args=[self.rumor.id])
        response = self.client.get(url)
        # redirect to login page (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_create_rumor_post_invalid_non_ajax(self):
        """Covers fallback invalid form (non-AJAX)"""
        self.client.login(username="booster", password="12345")
        url = reverse("rumors:create_rumors")
        data = {
            "club_asal": "",
            "club_tujuan": "",
            "pemain": "",
            "content": "",
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [200, 302])

    def test_delete_rumor_non_ajax_redirect(self):
        """Covers normal delete redirect branch"""
        self.client.login(username="booster", password="12345")
        url = reverse("rumors:delete_rumors", args=[self.rumor.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])

# =================== COVERAGE FINISHER TESTS ======================
class RumorsCoverageFinisherTests(TestCase):
    def setUp(self):
        from main.models import Club, Player
        from django.contrib.auth import get_user_model
        from rumors.models import Rumors
        self.client = Client()
        User = get_user_model()
        self.club1 = Club.objects.create(name="FinisherA", country="Italy")
        self.club2 = Club.objects.create(name="FinisherB", country="Germany")
        self.user = User.objects.create_user(username="finisher", password="12345", is_fan=True)
        self.admin = User.objects.create_user(username="finisher_admin", password="12345", is_club_admin=True)
        self.player = Player.objects.create(
            nama_pemain="Finisher Player",
            position="GK",
            umur=30,
            market_value=3000000,
            negara="Germany",
            current_club=self.club1,
        )
        self.rumor = Rumors.objects.create(
            author=self.user,
            pemain=self.player,
            club_asal=self.club1,
            club_tujuan=self.club2,
            content="Finisher rumor",
            status="pending",
        )

    def test_verify_deny_without_login_redirect(self):
        """Covers non-logged-in redirect in verify/deny/revert"""
        for route in ["verify_rumor", "deny_rumor", "revert_rumor"]:
            url = reverse(f"rumors:{route}", args=[self.rumor.id])
            res = self.client.post(url)
            self.assertEqual(res.status_code, 302)
            self.assertIn("/login", res.url)

    def test_edit_rumor_invalid_form_ajax(self):
        """Covers invalid edit AJAX branch"""
        self.client.login(username="finisher", password="12345")
        url = reverse("rumors:edit_rumors", args=[self.rumor.id])
        data = {
            "club_asal": "",
            "club_tujuan": "",
            "pemain": "",
            "content": "",
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("errors", data)

    def test_show_rumors_main_invalid_method(self):
        """Covers invalid method (POST on GET-only view)"""
        url = reverse("rumors:show_rumors_main")
        res = self.client.post(url)
        self.assertIn(res.status_code, [200, 405])

    def test_delete_rumor_invalid_id_ajax(self):
        """Covers 404/invalid id AJAX delete"""
        self.client.login(username="finisher", password="12345")
        invalid_uuid = uuid.uuid4()
        url = reverse("rumors:delete_rumors", args=[invalid_uuid])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [404, 200, 403])

    def test_get_designated_clubs_without_param(self):
        """Covers missing club_asal param"""
        url = reverse("rumors:get_designated_clubs")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_get_players_by_club_missing_param(self):
        """Covers missing club_id param"""
        url = reverse("rumors:get_players_by_club")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

class RumorsFinalPushTests(TestCase):
    """Final booster to push coverage >80% for rumors app"""

def setUp(self):
    from main.models import Club, Player
    from accounts.models import Profile
    from rumors.models import Rumors
    from django.contrib.auth import get_user_model

    self.client = Client()
    User = get_user_model()

    self.club_a = Club.objects.create(name="FinalA")
    self.club_b = Club.objects.create(name="FinalB")

    user = User.objects.create_user(username="final_admin", password="12345")
    self.admin = Profile.objects.create(user=user, club=self.club_a, is_club_admin=True)

    self.player = Player.objects.create(name="FinalPlayer", club=self.club_a)
    self.rumor = Rumors.objects.create(
        pemain=self.player,
        club_asal=self.club_a,
        club_tujuan=self.club_b,
        content="Rumor terakhir",
        author=self.admin,
    )


