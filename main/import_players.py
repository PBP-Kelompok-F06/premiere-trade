import pandas as pd
from player_transaction.models import Player, Club
import uuid

def import_players_from_excel(filepath):
    # Baca file Excel
    df = pd.read_excel(filepath)

    for _, row in df.iterrows():
        # Ambil atau buat Club terlebih dahulu
        club, _ = Club.objects.get_or_create(
            name=row['club_name'],
            defaults={
                'country': row.get('country', ''),
                'logo_url': row.get('logo_url', '')
            }
        )

        # Buat Player baru
        player = Player.objects.create(
            current_club=club,
            id=uuid.uuid4(),
            nama_pemain=row['nama_pemain'],
            position=row['position'],
            umur=row['umur'],
            market_value=row['market_value'],
            negara=row['negara'],
            jumlah_goal=row['jumlah_goal'],
            jumlah_asis=row['jumlah_asis'],
            jumlah_match=row['jumlah_match'],
            sedang_dijual=False,  # default belum dijual
        )

        print(f"✅ Tambah {player.nama_pemain} ke klub {club.name}")

    print("🎉 Import selesai!")
