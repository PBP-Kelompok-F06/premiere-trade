import pandas as pd
import re

# Nama file Anda
file_asli = "transfermarkt_data.csv"
file_lengkap = "transfermarkt_data_LENGKAP.xlsx"

# 1. Baca kedua file CSV
try:
    df_asli = pd.read_csv(file_asli)
    df_lengkap = pd.read_csv(file_lengkap)
except FileNotFoundError as e:
    print(f"Error: File tidak ditemukan. Pastikan file '{e.filename}' ada di folder yang sama.")
    exit()

# 2. Buat "kamus" (mapping) dari file lengkap
# Kita akan memetakan 'Nama' ke 'Posisi' dan 'Nama' ke string 'Market Value' (yang berisi umur)
# Kita ganti nama kolom 'Market Value' di file lengkap agar tidak bentrok
df_lengkap = df_lengkap.rename(columns={"Market Value": "DOB_Age_String"})

# Buat kamus (dictionary) untuk mapping
# .set_index('Nama') membuat 'Nama' menjadi key
posisi_map = df_lengkap.set_index('Nama')['Posisi'].to_dict()
dob_age_map = df_lengkap.set_index('Nama')['DOB_Age_String'].to_dict()

# 3. Update DataFrame asli menggunakan .map()
# 'nama_pemain' di df_asli akan dicocokkan dengan key di 'posisi_map'
df_asli['posisi'] = df_asli['nama_pemain'].map(posisi_map)

# Kita buat kolom sementara untuk string umur, lalu ekstrak umurnya
df_asli['temp_dob_age'] = df_asli['nama_pemain'].map(dob_age_map)

# 4. Ekstrak umur dari string (e.g., "18 Nov 1997 (27)" -> "27")
# .str.extract(r'\((\d+)\)') akan mencari angka di dalam tanda kurung
df_asli['umur'] = df_asli['temp_dob_age'].str.extract(r'\((\d+)\)')

# 5. Isi N/A jika ada pemain yang tidak ditemukan di file lengkap
df_asli['posisi'] = df_asli['posisi'].fillna('N/A')
df_asli['umur'] = df_asli['umur'].fillna('N/A')

# 6. Hapus kolom sementara
df_asli = df_asli.drop(columns=['temp_dob_age'])

# 7. Tampilkan hasil
print("--- Dataframe setelah di-update ---")
print(df_asli)

# 8. Simpan ke file CSV baru (opsional)
output_filename = "transfermarkt_data_FINAL.csv"
df_asli.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"\nData berhasil disimpan ke {output_filename}")