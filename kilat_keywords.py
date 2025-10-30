"""
Kilat-Lang Keyword Mappings
Malay-syntax programming language based on Python
"""

# Mapping of Kilat-Lang (Malay) keywords to Python keywords
KILAT_TO_PYTHON = {
    # Control Flow
    'jika': 'if',
    'atau': 'else',
    'ataujika': 'elif',
    'untuk diulang': 'for',
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
    'atau_logik': 'or',
    'bukan': 'not',
    'dalam': 'in',
    'tidak_dalam': 'not in',
    'adalah': 'is',
    'bukan_adalah': 'is not',
    
    # Exception Handling
    'cuba': 'try',
    'tangkap': 'except',
    'akhirnya': 'finally',
    'bangkit': 'raise',
    'tegas': 'assert',
    
    # Import
    'import': 'import',
    'dari': 'from',
    'sebagai': 'as',
    
    # Other
    'dengan': 'with',
    'berikan': 'yield',
    'global': 'global',
    'nonlokal': 'nonlocal',
    'padam': 'del',
    
    # Built-in functions (common ones)
    'cetak': 'print',
    'input': 'input',
    'panjang': 'len',
    'julat': 'range',
    'jenis': 'type',
    'str': 'str',
    'int': 'int',
    'float': 'float',
    'list': 'list',
    'dict': 'dict',
    'set': 'set',
    'tuple': 'tuple',
}

# Reverse mapping for reference
PYTHON_TO_KILAT = {v: k for k, v in KILAT_TO_PYTHON.items()}
