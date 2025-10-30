# Kilat-Lang ⚡

**Bahasa Pengaturcaraan Berdasarkan Python dengan Sintaks Melayu**

Kilat-Lang adalah bahasa pengaturcaraan yang menggunakan sintaks Bahasa Melayu tetapi berdasarkan Python. Ia direka untuk memudahkan pembelajaran pengaturcaraan dalam Bahasa Melayu.

## 🌟 Ciri-ciri

- ✅ Sintaks Bahasa Melayu yang mudah difahami
- ✅ Berdasarkan Python (backward compatible)
- ✅ Sokongan penuh untuk fungsi, kelas, dan modul
- ✅ Compiler/interpreter yang mudah digunakan
- ✅ Contoh program yang lengkap

## 📦 Keperluan

- Python 3.6 atau lebih tinggi

## 🚀 Cara Menggunakan

Kilat-Lang mempunyai **DUA mod pelaksanaan**:

### 1. Mod Transpile (Default) - Bergantung kepada Python

```bash
python kilat.py <nama_fail.klt>
```

Menterjemah kod Kilat kepada Python dan menjalankannya.

Contoh:
```bash
python kilat.py examples/hello_world.klt
```

### 2. Mod Native - Interpreter Bebas

```bash
python kilat.py <nama_fail.klt> --native
```

Menjalankan kod Kilat terus tanpa bergantung kepada Python! Menggunakan lexer, parser, dan interpreter tersendiri.

Contoh:
```bash
python kilat.py examples/hello_world.klt --native
```

### 3. Compile Sahaja (Tanpa Jalankan)

```bash
python kilat.py <nama_fail.klt> --compile-only
```

Ini akan menghasilkan fail Python (`.py`) yang boleh dijalankan kemudian.

### 4. Compile dengan Nama Output Tertentu

```bash
python kilat.py <nama_fail.klt> --compile-only -o output.py
```

## 📖 Sintaks Kilat-Lang

### Kata Kunci Asas

| Kilat-Lang | Python | Keterangan |
|------------|--------|------------|
| `cetak` | `print` | Cetak output |
| `jika` | `if` | Pernyataan bersyarat |
| `atau` | `else` | Else statement |
| `ataujika` | `elif` | Else-if statement |
| `untuk diulang` | `for` | For loop |
| `selagi` | `while` | While loop |
| `fungsi` | `def` | Definisi fungsi |
| `kelas` | `class` | Definisi kelas |
| `kembali` | `return` | Return statement |
| `benar` | `True` | Boolean true |
| `salah` | `False` | Boolean false |
| `tiada` | `None` | None value |
| `dan` | `and` | Logical AND |
| `atau_logik` | `or` | Logical OR |
| `bukan` | `not` | Logical NOT |
| `dalam` | `in` | In operator |
| `julat` | `range` | Range function |
| `panjang` | `len` | Length function |

[Lihat senarai lengkap kata kunci dalam `kilat_keywords.py`]

## 💡 Contoh Program

### Hello World

```kilat
cetak("Selamat datang ke Kilat-Lang!")
```

### For Loop

```kilat
untuk diulang i dalam julat(1, 6):
    cetak("Nombor:", i)
```

### Pernyataan Bersyarat

```kilat
umur = 20

jika umur >= 18:
    cetak("Anda dewasa")
atau:
    cetak("Anda masih kanak-kanak")
```

### Fungsi

```kilat
fungsi tambah(a, b):
    kembali a + b

hasil = tambah(5, 3)
cetak("Hasil:", hasil)
```

### Kelas

```kilat
kelas Orang:
    fungsi __init__(self, nama):
        self.nama = nama
    
    fungsi salam(self):
        cetak("Salam,", self.nama)

orang = Orang("Ahmad")
orang.salam()
```

## 📂 Struktur Projek

```
Kilat-Lang/
├── kilat.py                 # Compiler/interpreter utama
├── kilat_keywords.py        # Pemetaan kata kunci
├── kilat_lexer.py          # Lexer untuk tokenization
├── kilat_translator.py     # Translator Kilat -> Python
├── examples/               # Contoh program
│   ├── hello_world.klt
│   ├── for_loop.klt
│   ├── conditionals.klt
│   ├── functions.klt
│   ├── classes.klt
│   └── calculator.klt
└── README.md
```

## 🎯 Contoh Lengkap

Lihat folder `examples/` untuk contoh program yang lengkap:

1. **hello_world.klt** - Program Hello World asas
2. **for_loop.klt** - Contoh penggunaan for loop
3. **conditionals.klt** - Pernyataan bersyarat (if-else)
4. **functions.klt** - Definisi dan penggunaan fungsi
5. **classes.klt** - Pengaturcaraan berorientasikan objek
6. **calculator.klt** - Kalkulator mudah (program lengkap)

## 🧪 Menguji Compiler

Jalankan semua contoh program untuk menguji compiler:

```bash
# Hello World
python kilat.py examples/hello_world.klt

# For Loop
python kilat.py examples/for_loop.klt

# Conditionals
python kilat.py examples/conditionals.klt

# Functions
python kilat.py examples/functions.klt

# Classes
python kilat.py examples/classes.klt

# Calculator
python kilat.py examples/calculator.klt
```

## 🔧 Cara Kerja

### Mod Transpile (Default)
1. **Lexer** (`kilat_lexer.py`) - Membaca kod Kilat-Lang dan menukar kata kunci Melayu kepada token Python
2. **Translator** (`kilat_translator.py`) - Menterjemah token kepada kod Python yang sah
3. **Compiler** (`kilat.py`) - Menjalankan kod Python yang telah diterjemah

### Mod Native (--native)
1. **Lexer** (`kilat_lexer2.py`) - Tokenisasi kod sumber kepada tokens
2. **Parser** (`kilat_parser.py`) - Membina Abstract Syntax Tree (AST)
3. **Interpreter** (`kilat_interpreter.py`) - Melaksanakan AST secara langsung

**Lihat [ARCHITECTURE.md](ARCHITECTURE.md) untuk penjelasan lengkap tentang arkitektur compiler.**

## 🤝 Sumbangan

Sumbangan adalah dialu-alukan! Anda boleh:
- Menambah kata kunci baharu
- Memperbaiki translator
- Menambah contoh program
- Melaporkan bug

## 📝 Lesen

Projek ini adalah open source dan tersedia untuk kegunaan pendidikan.

## 👨‍💻 Penulis

Kilat-Lang - Bahasa pengaturcaraan Melayu untuk semua!

---

**Selamat mengaturcara dengan Kilat-Lang! ⚡**
