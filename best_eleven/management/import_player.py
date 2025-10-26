from django.core.management.base import BaseCommand
from best_eleven.models import Player, Club
from django.conf import settings
import os
import pandas as pd

class Command(BaseCommand):
    help = 'Mengimpor data pemain dari Dataset.xlsx ke database'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'Dataset.xlsx')

        position_map = {
            'Kiper': 'GK',
            'Bek-Tengah': 'DEF',
            'Bek-Kiri': 'DEF',
            'Bek-Kanan': 'DEF',
            'Gel. Bertahan': 'MID',
            'Gel. Tengah': 'MID',
            'Gel. Serang': 'MID',
            'Sayap Kiri': 'FWD',
            'Sayap Kanan': 'FWD',
            'Depan-Tengah': 'FWD',
        }

        self.stdout.write(self.style.SUCCESS(f'Memulai impor dari {file_path}...'))

        try:
            df = pd.read_excel(file_path)

            df.columns = df.columns.str.strip().str.lower()

            expected_cols = [
                'nama_pemain', 'klub', 'posisi', 'umur',
                'market_value', 'negara', 'jumlah_goal',
                'jumlah_asis', 'jumlah_match', 'url profile'
            ]
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                self.stdout.write(self.style.ERROR(f'Kolom berikut hilang di Excel: {missing_cols}'))
                return

            pemain_baru_count = 0
            pemain_dilewati_count = 0
            klub_baru_count = 0

            for _, row in df.iterrows():
                nama_pemain = row['nama_pemain']
                posisi = row['posisi']
                nama_klub = row['klub']
                negara = row['negara']
                market_value = row['market_value']
                profile_image_url = row['url profile']
                umur = row['umur']

                if pd.isna(nama_pemain) or pd.isna(posisi) or pd.isna(nama_klub):
                    self.stdout.write(self.style.WARNING(f"Melewatkan baris kosong: {row}"))
                    continue

                club_obj, created = Club.objects.get_or_create(name=nama_klub)
                if created:
                    klub_baru_count += 1

                posisi_model = position_map.get(posisi.strip(), 'MID')

                player, created = Player.objects.get_or_create(
                    name=nama_pemain.strip(),
                    defaults={
                        'club': club_obj,
                        'position': posisi_model,
                        'nationality': negara,
                        'market_value': market_value,
                        'profile_image_url': profile_image_url,
                    }
                )

                if created:
                    pemain_baru_count += 1
                else:
                    pemain_dilewati_count += 1

            self.stdout.write(self.style.SUCCESS("\n✅ IMPORT SELESAI ✅"))
            self.stdout.write(f"🏟️ Klub baru: {klub_baru_count}")
            self.stdout.write(f"⚽ Pemain baru: {pemain_baru_count}")
            self.stdout.write(f"↩️ Pemain dilewati (sudah ada): {pemain_dilewati_count}")

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File "{file_path}" tidak ditemukan! Pastikan Dataset.xlsx ada di root project.'))
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            self.stdout.write(traceback.format_exc())
