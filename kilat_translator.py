"""
Kilat-Lang Translator
Translates Kilat-Lang source code to Python
"""

from kilat_lexer import KilatLexer


class KilatTranslator:
    """Translator that converts Kilat-Lang to Python"""
    
    def __init__(self, source_code):
        self.source_code = source_code
        self.python_code = ""
        
    def translate(self):
        """
        Translate Kilat-Lang source to Python
        """
        # Create lexer and tokenize
        lexer = KilatLexer(self.source_code)
        translated_lines = lexer.tokenize()
        
        # Join lines back together
        self.python_code = '\n'.join(translated_lines)
        
        return self.python_code
    
    def get_python_code(self):
        """
        Get the translated Python code
        """
        return self.python_code
