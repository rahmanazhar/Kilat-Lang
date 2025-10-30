# Kilat-Lang: Two Execution Modes

## Mode 1: Transpiler (Default)
```
┌─────────────────────────────────────────────────────────┐
│                    Kilat Source Code                     │
│                     (program.klt)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 KilatLexer (Simple)                      │
│           • Keyword translation only                     │
│           • Malay → Python mapping                       │
│                kilat_lexer.py                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  KilatTranslator                         │
│           • String replacement                           │
│           • Minimal processing                           │
│               kilat_translator.py                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Python Source Code                      │
│           • Valid Python syntax                          │
│           • Ready to execute                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Python Interpreter (exec)                   │
│           • Uses Python's runtime                        │
│           • Fast execution                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
                  Output


## Mode 2: Native Interpreter (--native)
```
┌─────────────────────────────────────────────────────────┐
│                    Kilat Source Code                     │
│                     (program.klt)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  KilatLexer2 (Complete)                  │
│    • Tokenization (KEYWORD, NUMBER, STRING, etc.)        │
│    • Indentation tracking (INDENT/DEDENT)                │
│    • Position tracking (line, column)                    │
│               kilat_lexer2.py                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │  Token Stream   │
           │  [Token, ...]   │
           └────────┬────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                    KilatParser                           │
│           • Recursive descent parsing                    │
│           • Operator precedence                          │
│           • Syntax validation                            │
│                kilat_parser.py                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │   AST (Tree)     │
          │   ProgramNode    │
          │   ├─ IfNode      │
          │   ├─ ForNode     │
          │   └─ ...         │
          └────────┬─────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                 KilatInterpreter                         │
│           • Tree-walking execution                       │
│           • Environment management                       │
│           • Runtime type checking                        │
│           • Built-in functions                           │
│              kilat_interpreter.py                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Runtime Environment   │
        │  • Variables           │
        │  • Functions           │
        │  • Classes             │
        │  • Call stack          │
        └────────┬───────────────┘
                 │
                 ▼
              Output


## Architecture Comparison

### Transpiler Mode
```
Source → [Text Replace] → Python → [Python VM] → Output
         └─ kilat_*.py ─┘         └─ Built-in ─┘

Pros: Fast, full Python features
Cons: Depends on Python, limited control
```

### Native Mode
```
Source → [Lex] → Tokens → [Parse] → AST → [Interpret] → Output
         └─ Lexer ─┘     └─ Parser ─┘    └─ Interpreter ─┘

Pros: Independent, extensible, educational
Cons: Slower, limited features (for now)
```

## Component Details

### kilat_ast.py (AST Nodes)
```
ASTNode (base)
├─ Literals
│  ├─ NumberNode
│  ├─ StringNode
│  ├─ BooleanNode
│  └─ NoneNode
├─ Operations
│  ├─ BinaryOpNode (+, -, *, /, ==, !=, ...)
│  └─ UnaryOpNode (-, not)
├─ Control Flow
│  ├─ IfNode
│  ├─ WhileNode
│  ├─ ForNode
│  ├─ BreakNode
│  ├─ ContinueNode
│  └─ ReturnNode
├─ Functions
│  ├─ FunctionDefNode
│  └─ FunctionCallNode
├─ Classes
│  ├─ ClassDefNode
│  └─ (instances)
└─ Structures
   ├─ ListNode
   ├─ DictNode
   ├─ IndexNode
   └─ AttributeNode
```

### kilat_lexer2.py (Token Types)
```
TokenType (enum)
├─ Literals
│  ├─ NUMBER
│  ├─ STRING
│  ├─ BENAR (True)
│  ├─ SALAH (False)
│  └─ TIADA (None)
├─ Keywords
│  ├─ JIKA (if)
│  ├─ UNTUK (for)
│  ├─ FUNGSI (def)
│  └─ ... (30+ keywords)
├─ Operators
│  ├─ PLUS, MINUS, MULTIPLY, DIVIDE
│  ├─ EQ, NE, LT, GT, LE, GE
│  └─ DAN (and), ATAU_LOGIK (or)
└─ Delimiters
   ├─ LPAREN, RPAREN
   ├─ LBRACE, RBRACE
   ├─ COLON, COMMA, DOT
   └─ INDENT, DEDENT, NEWLINE
```

### kilat_interpreter.py (Runtime)
```
KilatInterpreter
├─ Environment (scope chain)
│  ├─ Global environment
│  └─ Local environments (stack)
├─ Built-in Functions
│  ├─ cetak() [print]
│  ├─ julat() [range]
│  ├─ panjang() [len]
│  └─ type conversions
├─ Execution
│  ├─ eval() - expressions
│  └─ execute() - statements
├─ User-Defined
│  ├─ KilatFunction
│  ├─ KilatClass
│  └─ KilatInstance
└─ Control Flow
   ├─ BreakException
   ├─ ContinueException
   └─ ReturnException
```

## File Structure

```
Kilat-Lang/
├── Core Compiler (Native Mode)
│   ├── kilat_ast.py          (150 lines) AST definitions
│   ├── kilat_lexer2.py        (400 lines) Tokenizer
│   ├── kilat_parser.py        (550 lines) Parser
│   └── kilat_interpreter.py   (470 lines) Interpreter
│
├── Transpiler (Default Mode)
│   ├── kilat_keywords.py      (80 lines)  Keyword map
│   ├── kilat_lexer.py         (130 lines) Simple lexer
│   └── kilat_translator.py    (40 lines)  Translator
│
├── Main Entry Point
│   └── kilat.py               (130 lines) CLI & orchestration
│
├── Examples
│   ├── hello_world.klt
│   ├── for_loop.klt
│   ├── conditionals.klt
│   ├── functions.klt
│   ├── classes.klt
│   └── calculator.klt
│
└── Documentation
    ├── README.md              User guide
    ├── REFERENCE.md           Language reference
    ├── ARCHITECTURE.md        Technical architecture
    └── COMPILER_OVERVIEW.md   What we built

Total: ~2,000 lines of code
```

## Usage Examples

```bash
# Transpiler mode (fast, full features)
python kilat.py program.klt

# Native mode (independent, educational)
python kilat.py program.klt --native

# Compile to Python only
python kilat.py program.klt --compile-only

# Specify output file
python kilat.py program.klt --compile-only -o output.py
```

## What Makes This Special

1. **Two Paradigms**: Can run as transpiler OR independent interpreter
2. **Educational**: Shows how real compilers work
3. **Production-Ready**: Transpiler mode for actual use
4. **Extensible**: Easy to add new features to native mode
5. **Complete**: All major compiler components implemented
6. **Documented**: Comprehensive documentation and examples

---

**Kilat-Lang: From Syntax Sugar to Complete Compiler! ⚡**
