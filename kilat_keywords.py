"""
Kilat-Lang Keyword Mappings
Malay-syntax programming language based on Python
"""

# Mapping of Kilat-Lang (Malay) keywords to Python keywords
KILAT_TO_PYTHON = {
    # Control Flow — new keywords
    'kalau': 'if',
    'kalau tidak': 'elif',
    'selain': 'else',
    'ulang': 'for',
    'selagi': 'while',
    'berhenti': 'break',
    'teruskan': 'continue',
    'kembali': 'return',
    'lulus': 'pass',

    # Functions and Classes
    'fungsi': 'def',
    'kelas': 'class',
    'lambda': 'lambda',

    # Boolean and Logic
    'benar': 'True',
    'salah': 'False',
    'tiada': 'None',
    'dan': 'and',
    'atau': 'or',
    'bukan': 'not',
    'dalam': 'in',
    'tidak_dalam': 'not in',
    'adalah': 'is',
    'bukan_adalah': 'is not',

    # Exception Handling
    'cuba': 'try',
    'kecuali': 'except',
    'akhirnya': 'finally',
    'cetuskan': 'raise',
    'tegas': 'assert',

    # Import
    'masuk': 'import',
    'dari': 'from',
    'sebagai': 'as',

    # Other
    'dengan': 'with',
    'berikan': 'yield',
    'global': 'global',
    'bukan lokal': 'nonlocal',
    'padam': 'del',

    # Built-in functions (common ones)
    'cetak': 'print',
    'input': 'input',
    'panjang': 'len',
    'julat': 'range',
    'jenis': 'type',
    'teks': 'str',
    'nombor': 'int',
    'perpuluhan': 'float',
    'list': 'list',
    'dict': 'dict',
    'set': 'set',
    'tuple': 'tuple',

    # Old keywords — backward compatibility
    'jika': 'if',
    'ataujika': 'elif',
    'untuk diulang': 'for',
    'atau_logik': 'or',
    'tangkap': 'except',
    'bangkit': 'raise',
    'import': 'import',
    'nonlokal': 'nonlocal',
    'str': 'str',
    'int': 'int',
    'float': 'float',
}

# Reverse mapping for reference
PYTHON_TO_KILAT = {v: k for k, v in KILAT_TO_PYTHON.items()}
