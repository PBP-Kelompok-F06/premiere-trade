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

#### 0. Modul `main`
* Menyediakan homepage, template dasar (`base.html`), dan mengelola data master untuk `Club` dan `Player`.
* **CRUD**:
    * **Create**: (Data Awal) Mengimpor data pemain dari dataset.
    * **Read**: Menampilkan halaman daftar klub dan daftar pemain yang bisa dilihat oleh semua pengguna.

#### 1. Modul `accounts`
* Mengelola otentikasi dan profil pengguna.
* **CRUD**:
    * **Create**: Registrasi untuk `Fan Account`.
    * **Read**: Melihat halaman profil.
    * **Update**: Mengedit informasi profil.
    * **Delete**: Menghapus akun.

#### 2. Modul `transactions`
* Mengelola seluruh alur bursa transfer.
* **CRUD**:
    * **Create**: `Admin Club` membuat `TransferListing` (menjual pemain) dan `Offer` (menawar pemain).
    * **Read**: Semua pengguna melihat bursa transfer. `Admin Club` melihat detail tawaran masuk/keluar.
    * **Update**: `Admin Club` menerima/menolak `Offer`. Status pemain diperbarui setelah transfer.
    * **Delete**: `Admin Club` membatalkan `TransferListing` atau `Offer`.

#### 3. Modul `best_eleven`
* Fitur bagi `Fan Account` untuk membuat formasi 11 pemain terbaik.
* **CRUD**:
    * **Create**: `Fan Account` membuat formasi baru.
    * **Read**: `Fan Account` melihat formasi yang telah disimpan.
    * **Update**: `Fan Account` mengubah pemain dalam formasi mereka.
    * **Delete**: `Fan Account` menghapus formasi.

#### 4. Modul `rumors`
* Platform bagi `Fan Account` untuk memposting dan membahas rumor transfer.
* **CRUD**:
    * **Create**: `Fan Account` membuat postingan rumor baru.
    * **Read**: Semua pengguna membaca daftar rumor.
    * **Update**: Pengguna mengedit postingan rumor milik mereka.
    * **Delete**: Pengguna menghapus postingan rumor milik mereka.

#### 5. Modul `community`
* Forum diskusi umum bagi `Fan Account`.
* **CRUD**:
    * **Create**: `Fan Account` membuat topik (`Thread`) atau balasan (`Post`) baru.
    * **Read**: Semua pengguna membaca forum.
    * **Update**: Pengguna mengedit `Thread` atau `Post` milik mereka.
    * **Delete**: Pengguna menghapus `Thread` atau `Post` milik mereka.

---

## Sumber Dataset

Data pemain dan klub yang digunakan dalam proyek ini mengacu pada informasi yang tersedia di website https://www.transfermarkt.co.id/.

---

## Tautan Proyek

* **Link PWS:** https://walyulahdi-maulana-premieretrade.pbp.cs.ui.ac.id/
* **Link Figma:** https://www.figma.com/design/I6KMf3j7b4tI8y5NRLraYK/Premiere-Trade