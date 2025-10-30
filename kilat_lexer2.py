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
    BENAR = auto()      # True
    SALAH = auto()      # False
    TIADA = auto()      # None
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Keywords - Control Flow
    JIKA = auto()       # if
    ATAUJIKA = auto()   # elif
    ATAU = auto()       # else
    UNTUK = auto()      # for
    DIULANG = auto()    # part of "untuk diulang"
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
    
    # Operators
    PLUS = auto()       # +
    MINUS = auto()      # -
    MULTIPLY = auto()   # *
    DIVIDE = auto()     # /
    FLOOR_DIV = auto()  # //
    MODULO = auto()     # %
    POWER = auto()      # **
    
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
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]  # Track indentation levels
        
    def error(self, message: str):
        raise SyntaxError(f"Lexer error at line {self.line}, column {self.column}: {message}")
    
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
                has_dot = True
            num_str += self.advance()
        
        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)
    
    def read_string(self, quote: str) -> Token:
        start_line, start_col = self.line, self.column
        self.advance()  # Skip opening quote
        string_value = ''
        
        while self.peek() and self.peek() != quote:
            if self.peek() == '\\':
                self.advance()
                next_char = self.advance()
                # Handle escape sequences
                escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', quote: quote}
                string_value += escape_map.get(next_char, next_char)
            else:
                string_value += self.advance()
        
        if not self.peek():
            self.error("Unterminated string")
        
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, string_value, start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.column
        identifier = ''
        
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            identifier += self.advance()
        
        # Check for multi-word keywords
        if identifier == 'untuk' and self.peek() == ' ':
            # Look ahead for "diulang"
            saved_pos = self.pos
            self.skip_whitespace()
            if self.peek() and self.source[self.pos:self.pos+7] == 'diulang':
                # Consume "diulang"
                for _ in range(7):
                    self.advance()
                return Token(TokenType.UNTUK, 'untuk diulang', start_line, start_col)
            else:
                self.pos = saved_pos
        
        token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        value = identifier
        
        # Convert boolean keywords to actual values
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
            self.error("Inconsistent indentation")
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code"""
        at_line_start = True
        
        while self.pos < len(self.source):
            # Handle indentation at line start
            if at_line_start:
                indent_level = 0
                while self.peek() in ' \t':
                    if self.peek() == ' ':
                        indent_level += 1
                    else:  # tab
                        indent_level += 4
                    self.advance()
                
                # Skip empty lines and comments
                if self.peek() in '\n\r' or self.peek() == '#':
                    self.skip_comment()
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
            if char == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
                at_line_start = True
                continue
            
            # Numbers
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Strings
            if char in '"\'':
                self.tokens.append(self.read_string(char))
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Two-character operators
            two_char = self.source[self.pos:self.pos+2]
            if two_char == '==':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
                continue
            elif two_char == '!=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NE, '!=', start_line, start_col))
                continue
            elif two_char == '<=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LE, '<=', start_line, start_col))
                continue
            elif two_char == '>=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GE, '>=', start_line, start_col))
                continue
            elif two_char == '//':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.FLOOR_DIV, '//', start_line, start_col))
                continue
            elif two_char == '**':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.POWER, '**', start_line, start_col))
                continue
            
            # Single-character tokens
            self.advance()
            if char == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            elif char == '-':
                self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
            elif char == '*':
                self.tokens.append(Token(TokenType.MULTIPLY, '*', start_line, start_col))
            elif char == '/':
                self.tokens.append(Token(TokenType.DIVIDE, '/', start_line, start_col))
            elif char == '%':
                self.tokens.append(Token(TokenType.MODULO, '%', start_line, start_col))
            elif char == '<':
                self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif char == '>':
                self.tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            elif char == '=':
                self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, ':', start_line, start_col))
            elif char == '.':
                self.tokens.append(Token(TokenType.DOT, '.', start_line, start_col))
            elif char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_col))
            else:
                self.error(f"Unexpected character: {char!r}")
        
        # Add remaining DEDENTs
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.column))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
