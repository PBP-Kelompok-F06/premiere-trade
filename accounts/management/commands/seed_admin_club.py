from django.core.management.base import BaseCommand
from accounts.models import CustomUser, Profile
from main.models import Club  # anggap kamu punya model Club

class Command(BaseCommand):
    help = "Membuat 4 admin club tetap dan hubungkan ke klub masing-masing"

    def handle(self, *args, **options):
        club_admins = {
            "chelsea": "Chelsea FC",
            "arsenal": "Arsenal FC",
            "manchester_city": "Manchester City",
            "liverpool": "Liverpool FC",
        }

        for username, club_name in club_admins.items():
            user, created = CustomUser.objects.get_or_create(
                username=f"admin_{username}",
                defaults={
                    "is_club_admin": True,
                    "is_fan": False,
                    "password": "12345"  # kamu bisa pakai set_password di bawah
                }
            )
            user.set_password("12345")
            user.save()

            # Buat atau hubungkan club
            club = Club.objects.get_or_create(nama_club=club_name)[0]

            # Hubungkan Profile
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.managed_club = club
            profile.save()

            print(f"✅ Admin untuk {club_name} dibuat atau diperbarui")
