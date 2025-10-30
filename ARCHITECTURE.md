# Kilat-Lang Architecture

## Overview

Kilat-Lang now supports **two execution modes**:

1. **Transpile Mode** (default): Translates Kilat code to Python and executes it
2. **Native Mode** (`--native`): Independent interpreter that runs Kilat code directly without Python

## Components

### 1. Original Transpiler (Python-dependent)
- **kilat_keywords.py**: Keyword mappings (Malay → Python)
- **kilat_lexer.py**: Simple lexer that translates keywords
- **kilat_translator.py**: Converts Kilat syntax to Python code

### 2. New Independent Compiler/Interpreter
- **kilat_ast.py**: Abstract Syntax Tree node definitions
- **kilat_lexer2.py**: Full-featured lexer with tokenization
- **kilat_parser.py**: Recursive descent parser (builds AST)
- **kilat_interpreter.py**: Tree-walking interpreter (executes AST)

## Compiler Architecture

```
Source Code (.klt)
        |
        v
    [LEXER] ---------> Tokens
        |
        v
    [PARSER] --------> AST (Abstract Syntax Tree)
        |
        v
  [INTERPRETER] ----> Execution (Runtime)
```

### Lexer (kilat_lexer2.py)
**Purpose**: Convert source code into tokens

**Features**:
- Recognizes keywords, identifiers, operators, literals
- Handles indentation (INDENT/DEDENT tokens)
- Tracks line and column numbers for error reporting
- Supports strings, numbers, booleans, comments

**Example**:
```kilat
jika x > 10:
    cetak("Besar")
```

**Tokens**:
```
JIKA, IDENTIFIER(x), GT, NUMBER(10), COLON, NEWLINE, INDENT,
IDENTIFIER(cetak), LPAREN, STRING("Besar"), RPAREN, NEWLINE, DEDENT
```

### Parser (kilat_parser.py)
**Purpose**: Build Abstract Syntax Tree from tokens

**Features**:
- Recursive descent parser
- Handles operator precedence
- Supports all language constructs:
  - Variables and assignments
  - Control flow (if/elif/else, while, for)
  - Functions and classes
  - Lists and dictionaries
  - Binary and unary operations
  - Exception handling (try/except/finally)

**Example AST**:
```
IfNode(
    condition=BinaryOpNode(
        left=IdentifierNode("x"),
        operator=">",
        right=NumberNode(10)
    ),
    then_body=[
        FunctionCallNode(
            function="cetak",
            arguments=[StringNode("Besar")]
        )
    ]
)
```

### Interpreter (kilat_interpreter.py)
**Purpose**: Execute AST directly

**Features**:
- Tree-walking interpreter
- Environment for variable storage
- Function call stack
- Class and instance support
- Built-in functions (cetak, julat, panjang, etc.)
- Exception handling

**Execution Flow**:
1. Traverse AST nodes
2. Evaluate expressions
3. Execute statements
4. Manage scopes and environments
5. Handle control flow (loops, conditionals, returns)

## Key Differences

| Feature | Transpile Mode | Native Mode |
|---------|---------------|-------------|
| **Dependency** | Requires Python runtime | Independent (but written in Python) |
| **Process** | Kilat → Python → Execute | Kilat → AST → Execute |
| **Speed** | Fast (Python optimized) | Slower (interpreted) |
| **Features** | Full Python compatibility | Core features only |
| **Debugging** | See Python code | Kilat-level errors |

## Language Features Supported

### Native Mode (--native)
✅ Variables and assignments
✅ Arithmetic operations (+, -, *, /, //, %, **)
✅ Comparison operators (==, !=, <, >, <=, >=)
✅ Logical operators (dan, atau_logik, bukan)
✅ If/elif/else statements
✅ For loops (untuk diulang)
✅ While loops (selagi)
✅ Break and continue
✅ Functions (fungsi) with parameters and defaults
✅ Return statements
✅ Classes (kelas) with inheritance
✅ Lists and dictionaries
✅ Indexing and attribute access
✅ Try/except/finally
✅ Built-in functions (cetak, julat, panjang, etc.)

### Transpile Mode (default)
✅ All native mode features
✅ Full Python standard library
✅ F-strings
✅ Keyword arguments
✅ Advanced Python features
✅ Import statements
✅ Generators and comprehensions

## How It Works

### Transpile Mode
```bash
python kilat.py program.klt
```
1. Read .klt file
2. Replace Malay keywords with Python keywords
3. Execute resulting Python code

### Native Mode
```bash
python kilat.py program.klt --native
```
1. Read .klt file
2. Lex: Convert to tokens
3. Parse: Build AST
4. Interpret: Execute AST directly

## Example Compilation

**Source (program.klt)**:
```kilat
fungsi tambah(a, b):
    kembali a + b

hasil = tambah(5, 3)
cetak("Hasil:", hasil)
```

**Transpile Mode Output** (Python):
```python
def tambah(a, b):
    return a + b

hasil = tambah(5, 3)
print("Hasil:", hasil)
```

**Native Mode** (AST):
```
ProgramNode(
    statements=[
        FunctionDefNode(
            name="tambah",
            parameters=["a", "b"],
            body=[
                ReturnNode(
                    value=BinaryOpNode("+", a, b)
                )
            ]
        ),
        AssignmentNode(
            target="hasil",
            value=FunctionCallNode("tambah", [5, 3])
        ),
        FunctionCallNode("cetak", ["Hasil:", hasil])
    ]
)
```

## Advantages of Native Mode

1. **Language Independence**: No reliance on Python semantics
2. **Custom Features**: Can add Kilat-specific features
3. **Better Error Messages**: Kilat-level errors, not Python errors
4. **Educational**: Understanding how compilers work
5. **Portability**: Can compile to other targets (C, LLVM, bytecode)

## Future Enhancements

- [ ] Bytecode compiler + VM (faster execution)
- [ ] Type system and type checking
- [ ] Optimization passes
- [ ] Native code generation (compile to binary)
- [ ] Package manager
- [ ] Standard library in Kilat
- [ ] Debugging support (breakpoints, stepping)
- [ ] REPL (interactive mode)

## Performance

**Transpile Mode**: 
- Fast (uses Python's optimized runtime)
- Good for production use

**Native Mode**:
- Slower (tree-walking interpreter)
- Good for learning and development
- Can be improved with bytecode compilation

## Conclusion

Kilat-Lang demonstrates a complete compiler pipeline:
- **Lexical Analysis**: Breaking text into tokens
- **Syntax Analysis**: Building structured representation (AST)  
- **Semantic Analysis**: Understanding meaning (in interpreter)
- **Execution**: Running the program

The native mode makes Kilat-Lang a true independent language, not just a Python preprocessor!
