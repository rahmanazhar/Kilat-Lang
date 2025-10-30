"""
Kilat-Lang Lexer
Tokenizes Kilat-Lang source code
"""

import re
from kilat_keywords import KILAT_TO_PYTHON


class KilatLexer:
    """Lexer for tokenizing Kilat-Lang source code"""
    
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        
    def tokenize(self):
        """
        Tokenize the source code into keywords, identifiers, operators, etc.
        """
        # Split by lines to preserve structure
        lines = self.source_code.split('\n')
        
        for line in lines:
            self.tokens.append(self._tokenize_line(line))
            
        return self.tokens
    
    def _tokenize_line(self, line):
        """
        Tokenize a single line of code
        """
        # Preserve leading whitespace (indentation)
        indent = len(line) - len(line.lstrip())
        stripped_line = line.strip()
        
        # Empty line or comment
        if not stripped_line or stripped_line.startswith('#'):
            return line
        
        # Process the line
        result = ' ' * indent
        
        # Use regex to split by word boundaries while preserving strings
        # This regex captures strings, multi-word keywords, operators (multi-char first), and single chars
        pattern = r'(""".*?"""|\'\'\'.*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|untuk diulang|atau_logik|tidak_dalam|bukan_adalah|==|!=|<=|>=|//|\*\*|\w+|[^\w\s])'
        
        tokens = re.findall(pattern, stripped_line, re.DOTALL)
        
        translated_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Check if it's a string literal (preserve as-is)
            if (token.startswith('"') and token.endswith('"')) or \
               (token.startswith("'") and token.endswith("'")) or \
               (token.startswith('"""') and token.endswith('"""')) or \
               (token.startswith("'''") and token.endswith("'''")):
                translated_tokens.append(token)
            # Check if it's a Kilat keyword
            elif token in KILAT_TO_PYTHON:
                translated_tokens.append(KILAT_TO_PYTHON[token])
            # Check for multi-word keywords like "untuk diulang"
            elif token == 'untuk' and i + 1 < len(tokens) and tokens[i + 1] == 'diulang':
                translated_tokens.append(KILAT_TO_PYTHON['untuk diulang'])
                i += 1  # Skip next token
            else:
                # Keep as-is (identifiers, numbers, operators, etc.)
                translated_tokens.append(token)
            
            i += 1
        
        # Join tokens with appropriate spacing
        result += self._join_tokens(translated_tokens)
        
        return result
    
    def _join_tokens(self, tokens):
        """
        Join tokens with appropriate spacing
        """
        result = []
        operators = ['==', '!=', '<=', '>=', '//', '**', '=', '<', '>', '+', '-', '*', '/', '%']
        
        for i, token in enumerate(tokens):
            # Add token
            result.append(token)
            
            # Determine if we need space after this token
            if i < len(tokens) - 1:
                next_token = tokens[i + 1]
                
                # Don't add space before/after certain punctuation
                if token in ['(', '[', '{'] or next_token in [')', ']', '}', ',', ':', '.']:
                    continue
                elif token == '.':
                    continue  # No space after dot
                elif token in [')', ']', '}', ','] and next_token in ['(', '[', '{']:
                    continue
                elif token == ':':
                    continue
                # Don't add space after 'f' if followed by string (f-string)
                elif token == 'f' and next_token.startswith('"'):
                    continue
                elif token == 'f' and next_token.startswith("'"):
                    continue
                # Add space around operators
                elif token in operators or next_token in operators:
                    result.append(' ')
                else:
                    result.append(' ')
        
        return ''.join(result)
