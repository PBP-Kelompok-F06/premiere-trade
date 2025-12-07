import requests
from bs4 import BeautifulSoup
import pandas as pd
import re  # Untuk mengekstrak umur dari string
import time # Untuk memberi jeda antar request

# 1. Daftar URL dan Nama Klub
urls = {
    "Chelsea": "https://www.transfermarkt.co.id/chelsea-fc/kader/verein/631/saison_id/2025/plus/1",
    "Arsenal": "https://www.transfermarkt.co.id/arsenal-fc/kader/verein/11/saison_id/2025/plus/1",
    "Manchester City": "https://www.transfermarkt.co.id/manchester-city/kader/verein/281/saison_id/2025/plus/1",
    "Liverpool": "https://www.transfermarkt.co.id/fc-liverpool/kader/verein/31/saison_id/2025/plus/1"
}

# PENTING: Transfermarkt sering memblokir scraping.
# Header User-Agent ini menyamar sebagai browser biasa.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

all_players_data = [] # List untuk menampung data semua pemain

# Loop untuk setiap klub
for club_name, url in urls.items():
    print(f"Mengambil data untuk {club_name}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Cek jika ada error HTTP (spt 403 Forbidden)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Cari tabel pemain utama
        player_table = soup.find('table', {'class': 'items'})
        
        # Cari semua baris pemain (yang punya class 'odd' atau 'even')
        player_rows = player_table.find('tbody').find_all('tr', {'class': ['odd', 'even']})

        for row in player_rows:
            # 1. Nama Pemain dan Link Profile (untuk langkah selanjutnya)
            player_cell = row.find('td', {'class': 'hauptlink'})
            player_name = player_cell.text.strip()
            
            # Kita simpan link profil untuk Bagian 2 (Statistik)
            player_profile_link = "https://www.transfermarkt.co.id" + player_cell.find('a')['href']

            # 2. Klub
            club = club_name

            # 3. Umur (dari "tgl lahir (umur)")
            # Kolom DOB(Age) adalah kolom 'zentriert' pertama
            age_cell = row.find_all('td', {'class': 'zentriert'})[0] 
            age_text = age_cell.text.strip()
            # Gunakan regex untuk mencari angka di dalam kurung, misal "15 Mei 1999 (26)" -> "26"
            age_match = re.search(r'\((\d+)\)', age_text)
            age = age_match.group(1) if age_match else 'N/A'

            # 4. Negara (dari alt text gambar)
            # Kolom negara adalah 'zentriert' kedua dan berisi tag <img>
            country_cell = row.find_all('td', {'class': 'zentriert'})[1]
            country = country_cell.find('img')['alt'] if country_cell.find('img') else 'N/A'

            # 5. Posisi
            # Kolom posisi adalah 'zentriert' ketiga
            position = row.find_all('td', {'class': 'zentriert'})[2].text.strip()

            # 6. Market Value (Nilai Pasar)
            market_value_cell = row.find('td', {'class': 'rechts hauptlink'})
            market_value = market_value_cell.text.strip() if market_value_cell else 'N/A'


            # ---------------------------------------------------------------
            # BAGIAN 2: MENGAMBIL GOAL, ASSIST, MATCH (LOGIKA SULIT)
            # ---------------------------------------------------------------
            # Ini memerlukan request BARU ke 'player_profile_link'
            # Anda harus menambahkan jeda (time.sleep) agar tidak diblokir.
            # 
            # ---- CONTOH LOGIKA (TIDAK DIJALANKAN DI SINI) ----
            #
            # try:
            #    print(f"  -> Mengambil statistik untuk {player_name}...")
            #    time.sleep(1.5) # KASIH JEDA WAJIB!
            #    profile_resp = requests.get(player_profile_link, headers=headers)
            #    profile_soup = BeautifulSoup(profile_resp.text, 'html.parser')
            #    
            #    # Cari link ke 'Statistik terperinci' atau 'Semua musim'
            #    # (Selector ini HANYA CONTOH dan bisa berubah)
            #    stats_link_tag = profile_soup.find('a', string=re.compile(r'Statistik terperinci'))
            #    
            #    if stats_link_tag:
            #        stats_link = "https://www.transfermarkt.co.id" + stats_link_tag['href']
            #        time.sleep(1.5) # JEDA LAGI
            #        stats_resp = requests.get(stats_link, headers=headers)
            #        stats_soup = BeautifulSoup(stats_resp.text, 'html.parser')
            #        
            #        # Cari total di tabel statistik (biasanya di <tfoot>)
            #        # (Selector ini HANYA CONTOH dan bisa berubah)
            #        total_row = stats_soup.find('tfoot').find('tr')
            #        columns = total_row.find_all('td')
            #        
            #        # Sesuaikan indeks [2], [5], [6] berdasarkan tabel aslinya
            #        goals = columns[5].text.strip()
            #        assists = columns[6].text.strip()
            #        matches = columns[2].text.strip()
            #    else:
            #        goals, assists, matches = 'N/A', 'N/A', 'N/A'
            #
            # except Exception as e:
            #    print(f"  Error saat ambil stats {player_name}: {e}")
            #    goals, assists, matches = 'Error', 'Error', 'Error'
            #
            # ---- AKHIR CONTOH LOGIKA ----

            # Untuk contoh skrip ini, kita gunakan N/A (Belum Diambil)
            goals = 'N/A (Lihat Catatan)'
            assists = 'N/A (Lihat Catatan)'
            matches = 'N/A (Lihat Catatan)'


            # Masukkan data ke list
            player_data = {
                "nama_pemain": player_name,
                "klub": club,
                "posisi": position,
                "umur": age,
                "market_value": market_value,
                "negara": country,
                "jumlah_goal": goals,
                "jumlah_asis": assists,
                "jumlah_match": matches
            }
            all_players_data.append(player_data)

        print(f"Selesai mengambil data {club_name}. Menunggu 3 detik...")
        time.sleep(3) # Beri jeda antar request SETIAP TIM

    except requests.exceptions.RequestException as e:
        print(f"Gagal mengambil data untuk {club_name}: {e}")
    except Exception as e:
        print(f"Terjadi error saat memproses {club_name}: {e}")


# Konversi list of dictionaries ke DataFrame Pandas untuk tampilan kolom
df = pd.DataFrame(all_players_data)

print("\n--- HASIL SCRAPING (Data Tabel Utama) ---")
print(df)

# Anda bisa menyimpan ke CSV
df.to_csv("transfermarkt_data.csv", index=False)
print("\nData telah disimpan ke transfermarkt_data.csv")