import csv
from django.core.management.base import BaseCommand
from best_eleven.models import Player, Club  
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Mengimpor data pemain dari file dataset - dataset.csv ke database'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'dataset - dataset.csv')

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
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                pemain_baru_count = 0
                pemain_dilewati_count = 0
                klub_baru_count = 0

                for row in reader:
                    nama_pemain = row.get('nama_pemain')
                    posisi_csv = row.get('posisi')
                    nama_klub = row.get('klub') # <-- Ambil nama klub dari CSV

                    if not nama_pemain or not posisi_csv or not nama_klub:
                        self.stdout.write(self.style.WARNING(f"Melewatkan baris: data tidak lengkap {row}"))
                        continue

                    club_obj, created = Club.objects.get_or_create(name=nama_klub)
                    if created:
                        klub_baru_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  * Klub baru dibuat: {nama_klub}"))
                    
                    posisi_model = position_map.get(posisi_csv, 'MID') 

                    player, created = Player.objects.get_or_create(
                        name=nama_pemain,
                        defaults={
                            'club': club_obj, # <-- Hubungkan pemain ke klub
                            'position': posisi_model
                            'nationality': row.get('negara'),
                            'market_value': row.get('market_value'),
                            # 'profile_image_url': '...URL_FOTO_JIKA_ADA...'
                        }
                    )

                    if created:
                        pemain_baru_count += 1
                    else:
                        pemain_dilewati_count += 1

            self.stdout.write(self.style.SUCCESS(f'\nImpor Selesai!'))
            self.stdout.write(self.style.SUCCESS(f'{klub_baru_count} klub baru ditambahkan.'))
            self.stdout.write(self.style.SUCCESS(f'{pemain_baru_count} pemain baru ditambahkan.'))
            self.stdout.write(f'{pemain_dilewati_count} pemain dilewati (sudah ada).')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: File {file_path} tidak ditemukan.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Terjadi error: {e}'))