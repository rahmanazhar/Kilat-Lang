"""
Kilat-Lang Parser
Recursive descent parser that builds AST from tokens
"""

from typing import List, Optional, Union
from kilat_lexer2 import Token, TokenType, KilatLexer2
from kilat_ast import *


class KilatParser:
    """Recursive descent parser for Kilat-Lang"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def error(self, message: str):
        token = self.current_token()
        raise SyntaxError(f"Parser error at line {token.line}, column {token.column}: {message}")
    
    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def peek(self, offset: int = 0) -> Token:
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]
    
    def advance(self) -> Token:
        token = self.current_token()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            self.error(f"Expected {token_type.name}, got {token.type.name}")
        return self.advance()
    
    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> ProgramNode:
        """Parse the entire program"""
        statements = []
        self.skip_newlines()
        
        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return ProgramNode(statements=statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement"""
        self.skip_newlines()
        token = self.current_token()
        
        if token.type == TokenType.JIKA:
            return self.parse_if()
        elif token.type == TokenType.SELAGI:
            return self.parse_while()
        elif token.type == TokenType.UNTUK:
            return self.parse_for()
        elif token.type == TokenType.FUNGSI:
            return self.parse_function_def()
        elif token.type == TokenType.KELAS:
            return self.parse_class_def()
        elif token.type == TokenType.KEMBALI:
            return self.parse_return()
        elif token.type == TokenType.BERHENTI:
            self.advance()
            self.skip_newlines()
            return BreakNode(line=token.line, column=token.column)
        elif token.type == TokenType.TERUSKAN:
            self.advance()
            self.skip_newlines()
            return ContinueNode(line=token.line, column=token.column)
        elif token.type == TokenType.CUBA:
            return self.parse_try()
        elif token.type == TokenType.BANGKIT:
            return self.parse_raise()
        elif token.type == TokenType.IMPORT:
            return self.parse_import()
        elif token.type == TokenType.DARI:
            return self.parse_from_import()
        elif token.type == TokenType.LULUS:
            self.advance()
            self.skip_newlines()
            return None  # Pass statement does nothing
        else:
            return self.parse_expression_statement()
    
    def parse_expression_statement(self) -> ASTNode:
        """Parse an expression or assignment"""
        expr = self.parse_expression()
        
        # Check for assignment
        if self.current_token().type == TokenType.ASSIGN:
            if isinstance(expr, IdentifierNode):
                self.advance()  # Skip =
                value = self.parse_expression()
                self.skip_newlines()
                return AssignmentNode(target=expr.name, value=value, line=expr.line, column=expr.column)
            elif isinstance(expr, AttributeNode):
                # Handle attribute assignment (e.g., self.nama = value)
                self.advance()  # Skip =
                value = self.parse_expression()
                self.skip_newlines()
                return AttributeAssignmentNode(object=expr.object, attribute=expr.attribute, value=value, line=expr.line, column=expr.column)
            else:
                self.error("Invalid assignment target")
        
        self.skip_newlines()
        return expr
    
    def parse_block(self) -> List[ASTNode]:
        """Parse an indented block of statements"""
        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        
        statements = []
        while self.current_token().type not in [TokenType.DEDENT, TokenType.EOF]:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        if self.current_token().type == TokenType.DEDENT:
            self.advance()
        
        return statements
    
    def parse_if(self) -> IfNode:
        """Parse if statement"""
        token = self.expect(TokenType.JIKA)
        condition = self.parse_expression()
        then_body = self.parse_block()
        
        elif_parts = []
        else_body = None
        
        self.skip_newlines()
        
        # Handle elif
        while self.current_token().type == TokenType.ATAUJIKA:
            self.advance()
            elif_condition = self.parse_expression()
            elif_body = self.parse_block()
            elif_parts.append((elif_condition, elif_body))
            self.skip_newlines()
        
        # Handle else
        if self.current_token().type == TokenType.ATAU:
            self.advance()
            else_body = self.parse_block()
        
        return IfNode(
            condition=condition,
            then_body=then_body,
            elif_parts=elif_parts,
            else_body=else_body,
            line=token.line,
            column=token.column
        )
    
    def parse_while(self) -> WhileNode:
        """Parse while loop"""
        token = self.expect(TokenType.SELAGI)
        condition = self.parse_expression()
        body = self.parse_block()
        
        return WhileNode(condition=condition, body=body, line=token.line, column=token.column)
    
    def parse_for(self) -> ForNode:
        """Parse for loop"""
        token = self.expect(TokenType.UNTUK)
        
        var_token = self.expect(TokenType.IDENTIFIER)
        variable = var_token.value
        
        self.expect(TokenType.DALAM)
        iterable = self.parse_expression()
        body = self.parse_block()
        
        return ForNode(variable=variable, iterable=iterable, body=body, line=token.line, column=token.column)
    
    def parse_function_def(self) -> FunctionDefNode:
        """Parse function definition"""
        token = self.expect(TokenType.FUNGSI)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LPAREN)
        parameters = []
        defaults = []
        
        while self.current_token().type != TokenType.RPAREN:
            param_token = self.expect(TokenType.IDENTIFIER)
            parameters.append(param_token.value)
            
            # Check for default value
            if self.current_token().type == TokenType.ASSIGN:
                self.advance()
                defaults.append(self.parse_expression())
            
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        
        return FunctionDefNode(
            name=name,
            parameters=parameters,
            defaults=defaults,
            body=body,
            line=token.line,
            column=token.column
        )
    
    def parse_class_def(self) -> ClassDefNode:
        """Parse class definition"""
        token = self.expect(TokenType.KELAS)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        base_class = None
        if self.current_token().type == TokenType.LPAREN:
            self.advance()
            if self.current_token().type == TokenType.IDENTIFIER:
                base_class = self.advance().value
            self.expect(TokenType.RPAREN)
        
        body = self.parse_block()
        
        return ClassDefNode(name=name, base_class=base_class, body=body, line=token.line, column=token.column)
    
    def parse_return(self) -> ReturnNode:
        """Parse return statement"""
        token = self.expect(TokenType.KEMBALI)
        value = None
        
        if self.current_token().type not in [TokenType.NEWLINE, TokenType.EOF]:
            value = self.parse_expression()
        
        self.skip_newlines()
        return ReturnNode(value=value, line=token.line, column=token.column)
    
    def parse_try(self) -> TryNode:
        """Parse try-except statement"""
        token = self.expect(TokenType.CUBA)
        try_body = self.parse_block()
        
        except_clauses = []
        self.skip_newlines()
        
        while self.current_token().type == TokenType.TANGKAP:
            self.advance()
            exception_type = None
            if self.current_token().type == TokenType.IDENTIFIER:
                exception_type = self.advance().value
            except_body = self.parse_block()
            except_clauses.append((exception_type, except_body))
            self.skip_newlines()
        
        finally_body = None
        if self.current_token().type == TokenType.AKHIRNYA:
            self.advance()
            finally_body = self.parse_block()
        
        return TryNode(
            try_body=try_body,
            except_clauses=except_clauses,
            finally_body=finally_body,
            line=token.line,
            column=token.column
        )
    
    def parse_raise(self) -> RaiseNode:
        """Parse raise statement"""
        token = self.expect(TokenType.BANGKIT)
        exception = self.parse_expression()
        self.skip_newlines()
        return RaiseNode(exception=exception, line=token.line, column=token.column)
    
    def parse_import(self) -> ImportNode:
        """Parse import statement"""
        token = self.expect(TokenType.IMPORT)
        module_token = self.expect(TokenType.IDENTIFIER)
        module = module_token.value
        
        alias = None
        if self.current_token().type == TokenType.SEBAGAI:
            self.advance()
            alias_token = self.expect(TokenType.IDENTIFIER)
            alias = alias_token.value
        
        self.skip_newlines()
        return ImportNode(module=module, alias=alias, line=token.line, column=token.column)
    
    def parse_from_import(self) -> FromImportNode:
        """Parse from-import statement"""
        token = self.expect(TokenType.DARI)
        module_token = self.expect(TokenType.IDENTIFIER)
        module = module_token.value
        
        self.expect(TokenType.IMPORT)
        
        names = []
        aliases = []
        
        while True:
            name_token = self.expect(TokenType.IDENTIFIER)
            names.append(name_token.value)
            
            alias = None
            if self.current_token().type == TokenType.SEBAGAI:
                self.advance()
                alias_token = self.expect(TokenType.IDENTIFIER)
                alias = alias_token.value
            aliases.append(alias)
            
            if self.current_token().type != TokenType.COMMA:
                break
            self.advance()
        
        self.skip_newlines()
        return FromImportNode(module=module, names=names, aliases=aliases, line=token.line, column=token.column)
    
    def parse_expression(self) -> ASTNode:
        """Parse an expression"""
        return self.parse_or()
    
    def parse_or(self) -> ASTNode:
        """Parse logical OR"""
        left = self.parse_and()
        
        while self.current_token().type == TokenType.ATAU_LOGIK:
            op_token = self.advance()
            right = self.parse_and()
            left = BinaryOpNode(left=left, operator='atau_logik', right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_and(self) -> ASTNode:
        """Parse logical AND"""
        left = self.parse_not()
        
        while self.current_token().type == TokenType.DAN:
            op_token = self.advance()
            right = self.parse_not()
            left = BinaryOpNode(left=left, operator='dan', right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_not(self) -> ASTNode:
        """Parse logical NOT"""
        if self.current_token().type == TokenType.BUKAN:
            op_token = self.advance()
            operand = self.parse_not()
            return UnaryOpNode(operator='bukan', operand=operand, line=op_token.line, column=op_token.column)
        
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparison operators"""
        left = self.parse_addition()
        
        while self.current_token().type in [TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE, TokenType.DALAM, TokenType.ADALAH]:
            op_token = self.advance()
            right = self.parse_addition()
            operator = op_token.value if op_token.type in [TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE] else op_token.type.name.lower()
            left = BinaryOpNode(left=left, operator=operator, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_addition(self) -> ASTNode:
        """Parse addition and subtraction"""
        left = self.parse_multiplication()
        
        while self.current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op_token = self.advance()
            right = self.parse_multiplication()
            left = BinaryOpNode(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_multiplication(self) -> ASTNode:
        """Parse multiplication, division, and modulo"""
        left = self.parse_power()
        
        while self.current_token().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.FLOOR_DIV, TokenType.MODULO]:
            op_token = self.advance()
            right = self.parse_power()
            left = BinaryOpNode(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_power(self) -> ASTNode:
        """Parse exponentiation"""
        left = self.parse_unary()
        
        if self.current_token().type == TokenType.POWER:
            op_token = self.advance()
            right = self.parse_power()  # Right associative
            return BinaryOpNode(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Parse unary operators"""
        if self.current_token().type == TokenType.MINUS:
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(operator='-', operand=operand, line=op_token.line, column=op_token.column)
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> ASTNode:
        """Parse postfix operations (calls, indexing, attribute access)"""
        expr = self.parse_primary()
        
        while True:
            token = self.current_token()
            
            if token.type == TokenType.LPAREN:
                # Function call
                self.advance()
                arguments = []
                while self.current_token().type != TokenType.RPAREN:
                    arguments.append(self.parse_expression())
                    if self.current_token().type == TokenType.COMMA:
                        self.advance()
                self.expect(TokenType.RPAREN)
                
                function_name = expr.name if isinstance(expr, IdentifierNode) else expr
                expr = FunctionCallNode(function=function_name, arguments=arguments, line=token.line, column=token.column)
            
            elif token.type == TokenType.LBRACKET:
                # Indexing
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexNode(object=expr, index=index, line=token.line, column=token.column)
            
            elif token.type == TokenType.DOT:
                # Attribute access
                self.advance()
                attr_token = self.expect(TokenType.IDENTIFIER)
                expr = AttributeNode(object=expr, attribute=attr_token.value, line=token.line, column=token.column)
            
            else:
                break
        
        return expr
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expressions"""
        token = self.current_token()
        
        # Numbers
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(value=token.value, line=token.line, column=token.column)
        
        # Strings
        if token.type == TokenType.STRING:
            self.advance()
            return StringNode(value=token.value, line=token.line, column=token.column)
        
        # Booleans
        if token.type == TokenType.BENAR:
            self.advance()
            return BooleanNode(value=True, line=token.line, column=token.column)
        
        if token.type == TokenType.SALAH:
            self.advance()
            return BooleanNode(value=False, line=token.line, column=token.column)
        
        # None
        if token.type == TokenType.TIADA:
            self.advance()
            return NoneNode(line=token.line, column=token.column)
        
        # Identifiers
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return IdentifierNode(name=token.value, line=token.line, column=token.column)
        
        # Lists
        if token.type == TokenType.LBRACKET:
            return self.parse_list()
        
        # Dicts
        if token.type == TokenType.LBRACE:
            return self.parse_dict()
        
        # Parenthesized expressions
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        self.error(f"Unexpected token: {token.type.name}")
    
    def parse_list(self) -> ListNode:
        """Parse list literal"""
        token = self.expect(TokenType.LBRACKET)
        elements = []
        
        while self.current_token().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RBRACKET)
        return ListNode(elements=elements, line=token.line, column=token.column)
    
    def parse_dict(self) -> DictNode:
        """Parse dictionary literal"""
        token = self.expect(TokenType.LBRACE)
        pairs = []
        
        while self.current_token().type != TokenType.RBRACE:
            key = self.parse_expression()
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            pairs.append((key, value))
            
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RBRACE)
        return DictNode(pairs=pairs, line=token.line, column=token.column)


def parse_kilat(source: str) -> ProgramNode:
    """Convenience function to lex and parse in one step"""
    lexer = KilatLexer2(source)
    tokens = lexer.tokenize()
    parser = KilatParser(tokens)
    return parser.parse()
