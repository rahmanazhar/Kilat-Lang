# Kilat-Lang Quick Reference Guide

## Kata Kunci Asas (Basic Keywords)

### Kawalan Aliran (Control Flow)
```kilat
jika x > 0:
    cetak("Positif")
ataujika x < 0:
    cetak("Negatif")
atau:
    cetak("Sifar")
```

### Gelung (Loops)
```kilat
# For loop
untuk diulang i dalam julat(5):
    cetak(i)

# While loop
selagi x < 10:
    x = x + 1
    
# Break dan Continue
untuk diulang i dalam julat(10):
    jika i == 5:
        berhenti
    jika i == 3:
        teruskan
    cetak(i)
```

### Fungsi (Functions)
```kilat
fungsi tambah(a, b):
    kembali a + b

hasil = tambah(5, 3)
```

### Kelas (Classes)
```kilat
kelas Kereta:
    fungsi __init__(self, warna):
        self.warna = warna
    
    fungsi pandu(self):
        cetak(f"Memandu kereta {self.warna}")

kereta = Kereta("merah")
kereta.pandu()
```

### Nilai Boolean (Boolean Values)
```kilat
x = benar      # True
y = salah      # False
z = tiada      # None
```

### Operator Logik (Logical Operators)
```kilat
jika x > 0 dan y > 0:
    cetak("Kedua-duanya positif")

jika x > 0 atau_logik y > 0:
    cetak("Sekurang-kurangnya satu positif")

jika bukan x:
    cetak("x adalah False")
```

### Built-in Functions
```kilat
cetak("Hello")          # print()
x = input("Nama: ")     # input()
p = panjang([1,2,3])   # len()
r = julat(10)          # range()
t = jenis(x)           # type()
```

## Senarai Lengkap Kata Kunci

| Kilat-Lang | Python | Keterangan |
|------------|--------|------------|
| `cetak` | `print` | Cetak output |
| `jika` | `if` | If statement |
| `atau` | `else` | Else statement |
| `ataujika` | `elif` | Elif statement |
| `untuk diulang` | `for` | For loop |
| `selagi` | `while` | While loop |
| `berhenti` | `break` | Break statement |
| `teruskan` | `continue` | Continue statement |
| `kembali` | `return` | Return statement |
| `lulus` | `pass` | Pass statement |
| `fungsi` | `def` | Function definition |
| `kelas` | `class` | Class definition |
| `lambda` | `lambda` | Lambda function |
| `benar` | `True` | Boolean true |
| `salah` | `False` | Boolean false |
| `tiada` | `None` | None value |
| `dan` | `and` | Logical AND |
| `atau_logik` | `or` | Logical OR |
| `bukan` | `not` | Logical NOT |
| `dalam` | `in` | In operator |
| `tidak_dalam` | `not in` | Not in operator |
| `adalah` | `is` | Is operator |
| `bukan_adalah` | `is not` | Is not operator |
| `cuba` | `try` | Try statement |
| `tangkap` | `except` | Except statement |
| `akhirnya` | `finally` | Finally statement |
| `bangkit` | `raise` | Raise exception |
| `tegas` | `assert` | Assert statement |
| `import` | `import` | Import statement |
| `dari` | `from` | From statement |
| `sebagai` | `as` | As statement |
| `dengan` | `with` | With statement |
| `berikan` | `yield` | Yield statement |
| `global` | `global` | Global keyword |
| `nonlokal` | `nonlocal` | Nonlocal keyword |
| `padam` | `del` | Delete statement |
| `julat` | `range` | Range function |
| `panjang` | `len` | Length function |
| `jenis` | `type` | Type function |

## Contoh Lengkap

### Program FizzBuzz
```kilat
untuk diulang i dalam julat(1, 21):
    jika i % 15 == 0:
        cetak("FizzBuzz")
    ataujika i % 3 == 0:
        cetak("Fizz")
    ataujika i % 5 == 0:
        cetak("Buzz")
    atau:
        cetak(i)
```

### Fungsi Rekursif
```kilat
fungsi fibonacci(n):
    jika n <= 1:
        kembali n
    atau:
        kembali fibonacci(n - 1) + fibonacci(n - 2)

untuk diulang i dalam julat(10):
    cetak(fibonacci(i))
```

### Exception Handling
```kilat
cuba:
    x = 10 / 0
tangkap ZeroDivisionError:
    cetak("Tidak boleh bahagi dengan sifar!")
akhirnya:
    cetak("Selesai")
```

## Tips

1. **Indentation**: Sama seperti Python, gunakan indentation (4 spaces atau 1 tab) untuk block code
2. **Case Sensitive**: Nama pembolehubah dan fungsi adalah case-sensitive
3. **Comments**: Gunakan `#` untuk comments
4. **String**: Gunakan `"` atau `'` untuk string
5. **F-strings**: Format string dengan `f"Nama: {nama}"`
