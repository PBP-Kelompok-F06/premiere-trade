# Premiere Trade

`Premiere Trade` merupakan website transfer jual beli pemain bola, di mana pemilik `Admin Club` dapat melakukan jual beli pemain pada website tersebut dengan sesama pemilik `Admin Club` lainnya. Terdapat juga `Fan Account` yang bisa melihat siapa saja pemain yang sedang dimasukkan ke dalam daftar transfer oleh setiap klub, serta melihat nilai pasar dari semua pemain yang ada.

---

## Anggota Kelompok

| Nama                          | NIM        |
| :---------------------------- | :--------- |
| Walyul'ahdi Maulana Ramadhan  | 2406426012 |
| Muhammad Indi Ryan Pratama    | 2406432160 |
| Salsabila Salimah             | 2406432734 |
| Aryandana Pascua Patiung      | 2406438214 |
| Adryan Muhammad Rasyad        | 2406430451 |

---

## Jenis Pengguna & Hak Akses

Proyek ini memiliki tiga jenis pengguna dengan hak akses yang berbeda:

### 1. Admin Club
* Melihat daftar pemain dari setiap klub.
* Melihat halaman bursa transfer.
* Melakukan transaksi penuh: menempatkan pemain untuk dijual, mengajukan penawaran, membeli, dan menerima/menolak tawaran dari klub lain.
* *Catatan: Setiap klub hanya memiliki satu akun admin.*

### 2. Fan Account
* Melihat daftar pemain dari setiap klub.
* Melihat halaman bursa transfer (hanya melihat, tidak bisa bertransaksi).
* *Catatan: Siapa pun dapat mendaftar sebagai Fan Account.*

### 3. User Non-Login
* Hanya dapat melihat daftar pemain dari setiap klub.

---

## Modul

#### 1. Modul `Players`
* **Backend**: Mengelola model dan data untuk `Player` dan `Club`. Data pemain akan diimpor dari dataset.
* **Frontend**: Menampilkan halaman daftar pemain dan klub yang dapat diakses publik.

#### 2. Modul `Accounts`
* **Backend**: Menangani proses Login, Registrasi (khusus `Fan Account`), pembuatan `Admin Club` secara manual (hardcode), dan manajemen otorisasi untuk setiap jenis pengguna.
* **Frontend**: Menyediakan antarmuka untuk halaman Login dan Registrasi.
* **Kalo ada waktu**: Fitur untuk mengedit informasi akun.

#### 3. Modul `Transfers`
* **Backend**: Menyediakan logika untuk memfilter dan mengambil data pemain yang sedang dijual untuk ditampilkan di halaman bursa transfer.
* **Frontend**: Merender halaman bursa transfer yang menampilkan semua pemain yang tersedia untuk dibeli.

#### 4. Modul `Sell`
* **Backend**: Mengimplementasikan logika untuk menambahkan pemain ke bursa transfer dan memproses persetujuan atau penolakan tawaran yang masuk.
* **Frontend**: Menyediakan halaman khusus bagi `Admin Club` untuk memilih pemain yang akan dijual dan mengelola tawaran.

#### 5. Modul `Buy`
* **Backend**: Mengimplementasikan logika untuk mengajukan penawaran (*bid*) terhadap pemain yang ada di bursa transfer.
* **Frontend**: Menyediakan antarmuka bagi `Admin Club` untuk mengajukan penawaran pada halaman bursa transfer.

---

## Sumber Dataset

Data pemain dan klub yang digunakan dalam proyek ini mengacu pada informasi yang tersedia di website https://www.transfermarkt.co.id/.

---

## Tautan Proyek

* **Link PWS:** https://walyulahdi-maulana-premieretrade.pbp.cs.ui.ac.id/
* **Link Figma:** https://www.figma.com/design/I6KMf3j7b4tI8y5NRLraYK/Premiere-Trade