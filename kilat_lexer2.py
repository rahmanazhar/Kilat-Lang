"""
Kilat-Lang Token Types and Lexer
Complete tokenizer for the language
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional
import re


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    FSTRING = auto()    # f"..." or f'...'  (raw content stored, parsed later)
    BENAR = auto()      # True
    SALAH = auto()      # False
    TIADA = auto()      # None

    # Identifiers
    IDENTIFIER = auto()

    # Keywords - Control Flow
    JIKA = auto()       # if
    ATAUJIKA = auto()   # elif
    ATAU = auto()       # else
    UNTUK = auto()      # for  (consumed as "untuk diulang")
    DIULANG = auto()    # part of "untuk diulang" (fallback if no space)
    SELAGI = auto()     # while
    BERHENTI = auto()   # break
    TERUSKAN = auto()   # continue
    KEMBALI = auto()    # return
    LULUS = auto()      # pass

    # Keywords - Functions and Classes
    FUNGSI = auto()     # def
    KELAS = auto()      # class

    # Keywords - Logical
    DAN = auto()        # and
    ATAU_LOGIK = auto() # or
    BUKAN = auto()      # not
    DALAM = auto()      # in
    ADALAH = auto()     # is

    # Keywords - Exception
    CUBA = auto()       # try
    TANGKAP = auto()    # except
    AKHIRNYA = auto()   # finally
    BANGKIT = auto()    # raise

    # Keywords - Import
    IMPORT = auto()
    DARI = auto()       # from
    SEBAGAI = auto()    # as

    # Keywords - Scope
    GLOBAL = auto()     # global
    NONLOKAL = auto()   # nonlocal

    # Keywords - Other
    PADAM = auto()      # del
    DENGAN = auto()     # with
    BERIKAN = auto()    # yield
    LAMBDA = auto()     # lambda

    # Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    MULTIPLY = auto()       # *
    DIVIDE = auto()         # /
    FLOOR_DIV = auto()      # //
    MODULO = auto()         # %
    POWER = auto()          # **

    # Augmented assignment operators
    PLUS_ASSIGN = auto()        # +=
    MINUS_ASSIGN = auto()       # -=
    STAR_ASSIGN = auto()        # *=
    SLASH_ASSIGN = auto()       # /=
    FLOOR_DIV_ASSIGN = auto()   # //=
    POWER_ASSIGN = auto()       # **=
    MODULO_ASSIGN = auto()      # %=

    # Comparison
    EQ = auto()         # ==
    NE = auto()         # !=
    LT = auto()         # <
    GT = auto()         # >
    LE = auto()         # <=
    GE = auto()         # >=

    # Assignment
    ASSIGN = auto()     # =

    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    COMMA = auto()      # ,
    COLON = auto()      # :
    DOT = auto()        # .
    SEMICOLON = auto()  # ;
    ARROW = auto()      # ->  (for future type hints)
    AT = auto()         # @   (for decorators)

    # Special
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class KilatLexer2:
    """Complete lexer for Kilat-Lang"""

    KEYWORDS = {
        'jika': TokenType.JIKA,
        'ataujika': TokenType.ATAUJIKA,
        'atau': TokenType.ATAU,
        'untuk': TokenType.UNTUK,
        'diulang': TokenType.DIULANG,
        'selagi': TokenType.SELAGI,
        'berhenti': TokenType.BERHENTI,
        'teruskan': TokenType.TERUSKAN,
        'kembali': TokenType.KEMBALI,
        'lulus': TokenType.LULUS,
        'fungsi': TokenType.FUNGSI,
        'kelas': TokenType.KELAS,
        'benar': TokenType.BENAR,
        'salah': TokenType.SALAH,
        'tiada': TokenType.TIADA,
        'dan': TokenType.DAN,
        'atau_logik': TokenType.ATAU_LOGIK,
        'bukan': TokenType.BUKAN,
        'dalam': TokenType.DALAM,
        'adalah': TokenType.ADALAH,
        'cuba': TokenType.CUBA,
        'tangkap': TokenType.TANGKAP,
        'akhirnya': TokenType.AKHIRNYA,
        'bangkit': TokenType.BANGKIT,
        'import': TokenType.IMPORT,
        'dari': TokenType.DARI,
        'sebagai': TokenType.SEBAGAI,
        'global': TokenType.GLOBAL,
        'nonlokal': TokenType.NONLOKAL,
        'padam': TokenType.PADAM,
        'dengan': TokenType.DENGAN,
        'berikan': TokenType.BERIKAN,
        'lambda': TokenType.LAMBDA,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]  # Track indentation levels

    def error(self, message: str):
        raise SyntaxError(f"Ralat leksikal di baris {self.line}, lajur {self.column}: {message}")

    def peek(self, offset: int = 0) -> Optional[str]:
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return None

    def advance(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self, skip_newline: bool = False):
        while self.peek() and self.peek() in ' \t\r' + ('\n' if skip_newline else ''):
            self.advance()

    def skip_comment(self):
        if self.peek() == '#':
            while self.peek() and self.peek() != '\n':
                self.advance()

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.column
        num_str = ''
        has_dot = False

        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if has_dot:
                    break
                # Make sure the next char after '.' is a digit (not another dot)
                if self.peek(1) and not self.peek(1).isdigit():
                    break
                has_dot = True
            num_str += self.advance()

        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def read_string(self, quote: str) -> Token:
        """Read a regular string (not f-string)."""
        start_line, start_col = self.line, self.column
        self.advance()  # Skip opening quote

        # Handle triple-quoted strings
        if self.peek() == quote and self.peek(1) == quote:
            self.advance()
            self.advance()
            return self._read_triple_string(quote, start_line, start_col)

        string_value = ''
        while self.peek() and self.peek() != quote:
            if self.peek() == '\n':
                self.error("Unterminated string (use triple quotes for multi-line)")
            if self.peek() == '\\':
                self.advance()
                next_char = self.advance()
                escape_map = {
                    'n': '\n', 't': '\t', 'r': '\r',
                    '\\': '\\', '"': '"', "'": "'",
                    '0': '\0',
                }
                string_value += escape_map.get(next_char, next_char)
            else:
                string_value += self.advance()

        if not self.peek():
            self.error("Unterminated string")

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, string_value, start_line, start_col)

    def _read_triple_string(self, quote: str, start_line: int, start_col: int) -> Token:
        """Read a triple-quoted string."""
        string_value = ''
        triple = quote * 3
        while self.pos < len(self.source):
            if self.source[self.pos:self.pos + 3] == triple:
                self.pos += 3
                self.column += 3
                return Token(TokenType.STRING, string_value, start_line, start_col)
            char = self.advance()
            string_value += char
        self.error("Unterminated triple-quoted string")

    def read_fstring(self, quote: str) -> Token:
        """Read an f-string; store raw content (without quotes)."""
        start_line, start_col = self.line, self.column
        self.advance()  # Skip opening quote

        # Handle triple f-strings
        if self.peek() == quote and self.peek(1) == quote:
            self.advance()
            self.advance()
            return self._read_fstring_content(quote * 3, start_line, start_col)

        return self._read_fstring_content(quote, start_line, start_col)

    def _read_fstring_content(self, closing: str, start_line: int, start_col: int) -> Token:
        """Read f-string content until closing quote(s)."""
        raw = ''
        is_triple = len(closing) == 3
        quote_char = closing[0]

        while self.pos < len(self.source):
            # Check for closing
            if is_triple:
                if self.source[self.pos:self.pos + 3] == closing:
                    self.pos += 3
                    self.column += 3
                    return Token(TokenType.FSTRING, raw, start_line, start_col)
            else:
                if self.peek() == closing:
                    self.advance()
                    return Token(TokenType.FSTRING, raw, start_line, start_col)

            if not is_triple and self.peek() == '\n':
                self.error("Unterminated f-string")

            # Handle escape sequences in f-strings
            if self.peek() == '\\':
                raw += self.advance()  # include backslash in raw
                if self.peek():
                    raw += self.advance()
            else:
                raw += self.advance()

        self.error("Unterminated f-string")

    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.column
        identifier = ''

        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            identifier += self.advance()

        # Check for multi-word keyword: "untuk diulang"
        if identifier == 'untuk':
            saved_pos = self.pos
            saved_line = self.line
            saved_col = self.column
            # Skip spaces
            spaces = ''
            while self.peek() == ' ':
                spaces += self.advance()
            if self.source[self.pos:self.pos + 7] == 'diulang':
                # Check that 'diulang' is a complete word
                end_pos = self.pos + 7
                if end_pos >= len(self.source) or not (self.source[end_pos].isalnum() or self.source[end_pos] == '_'):
                    for _ in range(7):
                        self.advance()
                    return Token(TokenType.UNTUK, 'untuk diulang', start_line, start_col)
            # Not a match, restore
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_col

        token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        value = identifier

        # Convert boolean/none keywords to Python values
        if token_type == TokenType.BENAR:
            value = True
        elif token_type == TokenType.SALAH:
            value = False
        elif token_type == TokenType.TIADA:
            value = None

        return Token(token_type, value, start_line, start_col)

    def handle_indentation(self, indent_level: int):
        """Handle INDENT and DEDENT tokens"""
        current_indent = self.indent_stack[-1]

        if indent_level > current_indent:
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, None, self.line, 1))

        while indent_level < self.indent_stack[-1]:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line, 1))

        if indent_level != self.indent_stack[-1]:
            self.error("Indentasi tidak konsisten")

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code"""
        at_line_start = True

        while self.pos < len(self.source):
            # Handle indentation at line start
            if at_line_start:
                indent_level = 0
                while self.peek() in ' \t':
                    if self.peek() == '\t':
                        indent_level = (indent_level // 4 + 1) * 4
                    else:
                        indent_level += 1
                    self.advance()

                # Skip empty lines and comment lines
                if self.peek() in ('\n', '\r', None) or self.peek() == '#':
                    self.skip_comment()
                    if self.peek() == '\n':
                        self.advance()
                    elif self.peek() == '\r':
                        self.advance()
                        if self.peek() == '\n':
                            self.advance()
                    continue

                self.handle_indentation(indent_level)
                at_line_start = False

            self.skip_whitespace(skip_newline=False)

            if not self.peek():
                break

            char = self.peek()
            start_line, start_col = self.line, self.column

            # Comments
            if char == '#':
                self.skip_comment()
                continue

            # Newline
            if char in ('\n', '\r'):
                self.advance()
                if char == '\r' and self.peek() == '\n':
                    self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
                at_line_start = True
                continue

            # Semicolon as statement separator (treat like newline)
            if char == ';':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, ';', start_line, start_col))
                continue

            # F-strings: f"..." or f'...'
            if char in ('f', 'F') and self.peek(1) in ('"', "'"):
                self.advance()  # consume f/F
                quote = self.peek()
                self.tokens.append(self.read_fstring(quote))
                continue

            # Numbers
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Strings
            if char in ('"', "'"):
                self.tokens.append(self.read_string(char))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Three-character operators (must check before two-char)
            three_char = self.source[self.pos:self.pos + 3]
            if three_char == '//=':
                self.advance(); self.advance(); self.advance()
                self.tokens.append(Token(TokenType.FLOOR_DIV_ASSIGN, '//=', start_line, start_col))
                continue
            elif three_char == '**=':
                self.advance(); self.advance(); self.advance()
                self.tokens.append(Token(TokenType.POWER_ASSIGN, '**=', start_line, start_col))
                continue

            # Two-character operators
            two_char = self.source[self.pos:self.pos + 2]
            two_char_map = {
                '==': TokenType.EQ,
                '!=': TokenType.NE,
                '<=': TokenType.LE,
                '>=': TokenType.GE,
                '//': TokenType.FLOOR_DIV,
                '**': TokenType.POWER,
                '+=': TokenType.PLUS_ASSIGN,
                '-=': TokenType.MINUS_ASSIGN,
                '*=': TokenType.STAR_ASSIGN,
                '/=': TokenType.SLASH_ASSIGN,
                '%=': TokenType.MODULO_ASSIGN,
                '->': TokenType.ARROW,
            }
            if two_char in two_char_map:
                self.advance(); self.advance()
                self.tokens.append(Token(two_char_map[two_char], two_char, start_line, start_col))
                continue

            # Single-character tokens
            self.advance()
            single_map = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '=': TokenType.ASSIGN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ':': TokenType.COLON,
                '.': TokenType.DOT,
                '@': TokenType.AT,
            }
            if char in single_map:
                self.tokens.append(Token(single_map[char], char, start_line, start_col))
            else:
                self.error(f"Aksara tidak dijangka: {char!r}")

        # Add remaining DEDENTs
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.column))

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
