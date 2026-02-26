# Kilat-Lang

**Bahasa Pengaturcaraan Berdasarkan Python dengan Sintaks Melayu**

Kilat-Lang ialah bahasa pengaturcaraan yang menggunakan kata kunci Bahasa Melayu. Ia direka untuk memudahkan pembelajaran pengaturcaraan dalam kalangan pelajar berbahasa Melayu, sambil mengekalkan kuasa dan fleksibiliti bahasa Python.

## Ciri-ciri

- Sintaks Bahasa Melayu yang mudah difahami
- Dua mod pelaksanaan: Transpile (bergantung Python) dan Native (interpreter bebas)
- Sokongan penuh: fungsi, kelas, warisan, pengendalian pengecualian, modul
- F-string, argumen kata kunci, tugasan bertambah (`+=`, `-=`, dll.)
- 123 ujian automatik — semua lulus
- Shell interaktif (REPL)
- 10 program contoh yang lengkap

## Keperluan

- Python 3.8 atau lebih tinggi
- Tiada kebergantungan pihak ketiga

## Pemasangan

```bash
git clone https://github.com/kilat-lang/kilat
cd kilat
```

Atau pasang sebagai pakej:

```bash
pip install -e .
```

## Cara Menggunakan

### Jalankan program

```bash
# Mod transpile (lalai) — terjemah ke Python lalu jalankan
python kilat.py program.klt

# Mod native — interpreter asli, tanpa kebergantungan Python
python kilat.py program.klt --native
```

### Shell interaktif (REPL)

```bash
python kilat.py --repl
```

```
Kilat-Lang REPL  (taip 'keluar' atau Ctrl+C untuk berhenti)
kilat> x = 10
kilat> cetak(x * 2)
20
kilat> keluar
```

### Kompil sahaja (tanpa jalankan)

```bash
python kilat.py program.klt --compile-only
python kilat.py program.klt --compile-only -o output.py
```

### Maklumat lain

```bash
python kilat.py --version
python kilat.py --help
```

## Sintaks Kilat-Lang

### Kata Kunci Lengkap

| Kilat-Lang | Python | Keterangan |
|---|---|---|
| `cetak` | `print` | Cetak output |
| `input` | `input` | Baca input pengguna |
| `jika` | `if` | Pernyataan bersyarat |
| `ataujika` | `elif` | Else-if |
| `atau` | `else` | Else |
| `untuk diulang` | `for` | Gelung for |
| `selagi` | `while` | Gelung while |
| `berhenti` | `break` | Keluar gelung |
| `teruskan` | `continue` | Terus ke ulangan berikut |
| `fungsi` | `def` | Definisi fungsi |
| `kelas` | `class` | Definisi kelas |
| `kembali` | `return` | Pulangkan nilai |
| `lulus` | `pass` | Tiada operasi |
| `benar` | `True` | Boolean benar |
| `salah` | `False` | Boolean salah |
| `tiada` | `None` | Nilai kosong |
| `dan` | `and` | DAN logik |
| `atau_logik` | `or` | ATAU logik |
| `bukan` | `not` | BUKAN logik |
| `dalam` | `in` | Operator keahlian |
| `adalah` | `is` | Operator identiti |
| `cuba` | `try` | Blok cuba |
| `tangkap` | `except` | Tangkap pengecualian |
| `akhirnya` | `finally` | Blok akhirnya |
| `bangkit` | `raise` | Bangkitkan pengecualian |
| `import` | `import` | Import modul |
| `dari` | `from` | Import dari |
| `sebagai` | `as` | Alias |
| `global` | `global` | Skop global |
| `nonlokal` | `nonlocal` | Skop bukan-lokal |
| `padam` | `del` | Padam pemboleh ubah |

### Fungsi Terbina (Built-in)

| Kilat-Lang | Keterangan |
|---|---|
| `cetak(...)` | Cetak nilai |
| `julat(n)` / `julat(a, b)` / `julat(a, b, l)` | Jana senarai nombor |
| `panjang(x)` | Bilangan elemen |
| `jenis(x)` | Jenis data |
| `abs(x)` | Nilai mutlak |
| `maks(senarai)` | Nilai maksimum |
| `min(senarai)` | Nilai minimum |
| `jumlah(senarai)` | Jumlah semua elemen |
| `disusun(senarai)` | Senarai tersusun (baru) |
| `terbalik(senarai)` | Senarai terbalik (baru) |
| `bulat(x)` | Bulatkan nombor |
| `int(x)` / `float(x)` / `str(x)` | Tukar jenis data |
| `peta(fungsi, senarai)` | Guna fungsi pada setiap elemen |
| `tapis(fungsi, senarai)` | Tapis elemen |
| `nombor_senarai(senarai)` | Tambah indeks (enumerate) |

## Contoh Program

### Hello World

```kilat
cetak("Selamat datang ke Kilat-Lang!")

nama = "Ahmad"
umur = 25
cetak(f"Nama: {nama}, Umur: {umur} tahun")
```

### Gelung dan Syarat

```kilat
untuk diulang i dalam julat(1, 11):
    jika i % 2 == 0:
        cetak(i, "genap")
    atau:
        cetak(i, "ganjil")
```

### Fungsi dengan Nilai Lalai

```kilat
fungsi salam(nama, bahasa="Melayu"):
    jika bahasa == "Melayu":
        cetak(f"Selamat datang, {nama}!")
    atau:
        cetak(f"Welcome, {nama}!")

salam("Ahmad")
salam("John", "Inggeris")
```

### Rekursi

```kilat
fungsi faktorial(n):
    jika n <= 1:
        kembali 1
    atau:
        kembali n * faktorial(n - 1)

cetak("5! =", faktorial(5))   # 120
cetak("10! =", faktorial(10)) # 3628800
```

### Kelas dan Warisan

```kilat
kelas Haiwan:
    fungsi __init__(self, nama, bunyi):
        self.nama = nama
        self.bunyi = bunyi

    fungsi buat_bunyi(self):
        cetak(f"{self.nama} kata '{self.bunyi}'")

kelas Anjing(Haiwan):
    fungsi __init__(self, nama):
        Haiwan.__init__(self, nama, "woof")

    fungsi ambil(self):
        cetak(f"{self.nama} ambil bola!")

buddy = Anjing("Buddy")
buddy.buat_bunyi()   # Buddy kata 'woof'
buddy.ambil()        # Buddy ambil bola!
```

### Pengendalian Pengecualian

```kilat
fungsi bahagi(a, b):
    jika b == 0:
        bangkit "Tidak boleh bahagi dengan sifar!"
    kembali a / b

cuba:
    cetak(bahagi(10, 2))    # 5.0
    cetak(bahagi(10, 0))    # akan bangkitkan pengecualian
tangkap:
    cetak("Ralat ditangkap!")
akhirnya:
    cetak("Selesai.")
```

### Tugasan Bertambah dan Kaedah Senarai

```kilat
nombor = [3, 1, 4, 1, 5, 9]
nombor.append(2)
nombor.sort()
cetak(nombor)               # [1, 1, 2, 3, 4, 5, 9]
cetak("Jumlah:", jumlah(nombor))
cetak("Maks:", maks(nombor))

kiraan = 0
untuk diulang n dalam nombor:
    kiraan += n
cetak("Kiraan manual:", kiraan)
```

### Import Modul

```kilat
import math
cetak(math.floor(3.9))      # 3

dari math import sqrt
cetak(int(sqrt(144)))       # 12
```

## Struktur Projek

```
Kilat-Lang/
├── kilat.py                  # Titik masuk CLI utama
├── kilat_ast.py              # Definisi nod AST
├── kilat_lexer2.py           # Pengtoken lengkap (mod native)
├── kilat_parser.py           # Parser penurunan rekursif
├── kilat_interpreter.py      # Interpreter berjalan-pokok
├── kilat_translator.py       # Penterjemah Kilat -> Python (mod transpile)
├── kilat_lexer.py            # Pengtoken mudah (mod transpile)
├── kilat_keywords.py         # Pemetaan kata kunci Melayu <-> Python
├── kilat_repl.py             # Shell interaktif (REPL)
├── test_native.py            # Suite 123 ujian automatik
├── pyproject.toml            # Konfigurasi pakej
└── examples/
    ├── hello_world.klt       # Program pertama
    ├── for_loop.klt          # Gelung for
    ├── conditionals.klt      # Pernyataan bersyarat
    ├── functions.klt         # Fungsi dan rekursi
    ├── classes.klt           # Kelas dan warisan
    ├── calculator.klt        # Kalkulator asas
    ├── senarai.klt           # Operasi senarai
    ├── rentetan.klt          # Operasi rentetan
    ├── cuba_tangkap.klt      # Pengendalian pengecualian
    └── kalkulator_lanjutan.klt  # Kalkulator berorientasikan objek
```

## Menguji

```bash
# Jalankan semua 123 ujian
python test_native.py

# Verbose (tunjuk setiap ujian)
python test_native.py -v
```

Kategori ujian: Aritmetik, Perbandingan, Pemboleh Ubah, Syarat, Gelung, Fungsi, Struktur Data, F-String, OOP, Pengecualian, Fungsi Terbina, Kaedah Rentetan, Kaedah Senarai, Skop, Import.

## Cara Kerja

### Mod Transpile (Lalai)

```
Kod Kilat (.klt)
      |
  [kilat_lexer.py]        — ganti kata kunci Melayu -> Python
      |
  [kilat_translator.py]   — hasilkan kod Python sah
      |
  Python exec()           — jalankan terus
```

### Mod Native (--native)

```
Kod Kilat (.klt)
      |
  [kilat_lexer2.py]       — tokenisasi penuh (38+ jenis token)
      |
  [kilat_parser.py]       — bina AST (penurunan rekursif)
      |
  [kilat_interpreter.py]  — laksanakan AST (tree-walking)
      |
  Output
```

Mod native melaksanakan keseluruhan saluran paip kompilasi (leksikal → sintaks → semantik → pelaksanaan) tanpa bergantung pada Python.

## Sumbangan

Sumbangan dialu-alukan:

- Tambah kata kunci baharu
- Perbaiki pengendalian ralat
- Tambah contoh program
- Lapor bug atau cadangkan ciri
- Tulis ujian tambahan

## Lesen

MIT License — bebas digunakan untuk tujuan pendidikan dan komersial.

---

**Selamat mengaturcara dengan Kilat-Lang!**
