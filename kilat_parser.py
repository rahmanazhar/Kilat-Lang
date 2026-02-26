"""
Kilat-Lang Parser
Recursive descent parser that builds AST from tokens
"""

from typing import Dict, List, Optional, Union
from kilat_lexer2 import Token, TokenType, KilatLexer2
from kilat_ast import *


class KilatParser:
    """Recursive descent parser for Kilat-Lang"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def error(self, message: str):
        token = self.current_token()
        raise SyntaxError(
            f"Ralat sintaks di baris {token.line}, lajur {token.column}: {message}"
        )

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def peek(self, offset: int = 1) -> Token:
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
            self.error(f"Dijangka {token_type.name}, dapat {token.type.name} ({token.value!r})")
        return self.advance()

    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()

    # ------------------------------------------------------------------ #
    #  Top-level                                                           #
    # ------------------------------------------------------------------ #

    def parse(self) -> ProgramNode:
        """Parse the entire program"""
        statements = []
        self.skip_newlines()

        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self.skip_newlines()

        return ProgramNode(statements=statements)

    # ------------------------------------------------------------------ #
    #  Statements                                                          #
    # ------------------------------------------------------------------ #

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
            return PassNode(line=token.line, column=token.column)
        elif token.type == TokenType.GLOBAL:
            return self.parse_global()
        elif token.type == TokenType.NONLOKAL:
            return self.parse_nonlocal()
        elif token.type == TokenType.PADAM:
            return self.parse_delete()
        else:
            return self.parse_expression_statement()

    def parse_expression_statement(self) -> ASTNode:
        """Parse an expression or assignment (including augmented assignment)."""
        expr = self.parse_expression()

        token = self.current_token()

        # Regular assignment: x = value, obj.attr = value, list[i] = value
        if token.type == TokenType.ASSIGN:
            self.advance()  # skip =
            value = self.parse_expression()
            self.skip_newlines()

            if isinstance(expr, IdentifierNode):
                return AssignmentNode(
                    target=expr.name, value=value,
                    line=expr.line, column=expr.column
                )
            elif isinstance(expr, AttributeNode):
                return AttributeAssignmentNode(
                    object=expr.object, attribute=expr.attribute,
                    value=value, line=expr.line, column=expr.column
                )
            elif isinstance(expr, IndexNode):
                return IndexAssignmentNode(
                    object=expr.object, index=expr.index,
                    value=value, line=expr.line, column=expr.column
                )
            else:
                self.error("Sasaran tugasan tidak sah")

        # Augmented assignments: +=, -=, *=, /=, //=, **=, %=
        aug_map = {
            TokenType.PLUS_ASSIGN:      '+',
            TokenType.MINUS_ASSIGN:     '-',
            TokenType.STAR_ASSIGN:      '*',
            TokenType.SLASH_ASSIGN:     '/',
            TokenType.FLOOR_DIV_ASSIGN: '//',
            TokenType.POWER_ASSIGN:     '**',
            TokenType.MODULO_ASSIGN:    '%',
        }
        if token.type in aug_map:
            op = aug_map[token.type]
            self.advance()  # skip operator
            value = self.parse_expression()
            self.skip_newlines()

            if isinstance(expr, IdentifierNode):
                return AugmentedAssignmentNode(
                    target=expr.name, operator=op,
                    value=value, line=expr.line, column=expr.column
                )
            elif isinstance(expr, IndexNode):
                # e.g., list[i] += 1  =>  list[i] = list[i] + 1
                # Store as special IndexAssignment with augmented op
                augmented_value = BinaryOpNode(
                    left=expr, operator=op,
                    right=value, line=expr.line, column=expr.column
                )
                return IndexAssignmentNode(
                    object=expr.object, index=expr.index,
                    value=augmented_value,
                    line=expr.line, column=expr.column
                )
            elif isinstance(expr, AttributeNode):
                augmented_value = BinaryOpNode(
                    left=expr, operator=op,
                    right=value, line=expr.line, column=expr.column
                )
                return AttributeAssignmentNode(
                    object=expr.object, attribute=expr.attribute,
                    value=augmented_value,
                    line=expr.line, column=expr.column
                )
            else:
                self.error("Sasaran tugasan bertambah tidak sah")

        self.skip_newlines()
        return expr

    def parse_block(self) -> List[ASTNode]:
        """Parse an indented block of statements"""
        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)

        statements = []
        while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self.skip_newlines()

        if self.current_token().type == TokenType.DEDENT:
            self.advance()

        return statements

    def parse_if(self) -> IfNode:
        token = self.expect(TokenType.JIKA)
        condition = self.parse_expression()
        then_body = self.parse_block()

        elif_parts = []
        else_body = None
        self.skip_newlines()

        while self.current_token().type == TokenType.ATAUJIKA:
            self.advance()
            elif_condition = self.parse_expression()
            elif_body = self.parse_block()
            elif_parts.append((elif_condition, elif_body))
            self.skip_newlines()

        if self.current_token().type == TokenType.ATAU:
            self.advance()
            else_body = self.parse_block()

        return IfNode(
            condition=condition, then_body=then_body,
            elif_parts=elif_parts, else_body=else_body,
            line=token.line, column=token.column
        )

    def parse_while(self) -> WhileNode:
        token = self.expect(TokenType.SELAGI)
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileNode(condition=condition, body=body, line=token.line, column=token.column)

    def parse_for(self) -> ForNode:
        token = self.expect(TokenType.UNTUK)
        var_token = self.expect(TokenType.IDENTIFIER)
        variable = var_token.value
        self.expect(TokenType.DALAM)
        iterable = self.parse_expression()
        body = self.parse_block()
        return ForNode(variable=variable, iterable=iterable, body=body,
                       line=token.line, column=token.column)

    def parse_function_def(self) -> FunctionDefNode:
        token = self.expect(TokenType.FUNGSI)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value

        self.expect(TokenType.LPAREN)
        parameters = []
        defaults = []

        while self.current_token().type != TokenType.RPAREN:
            param_token = self.expect(TokenType.IDENTIFIER)
            parameters.append(param_token.value)

            if self.current_token().type == TokenType.ASSIGN:
                self.advance()
                defaults.append(self.parse_expression())
            else:
                # Ensure required params come before default params
                if defaults:
                    self.error("Parameter biasa tidak boleh ikut parameter lalai")

            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RPAREN)

        # Optional return type annotation (ignored at runtime)
        if self.current_token().type == TokenType.ARROW:
            self.advance()
            self.parse_expression()  # consume type annotation

        body = self.parse_block()

        return FunctionDefNode(
            name=name, parameters=parameters, defaults=defaults,
            body=body, line=token.line, column=token.column
        )

    def parse_class_def(self) -> ClassDefNode:
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
        return ClassDefNode(name=name, base_class=base_class, body=body,
                            line=token.line, column=token.column)

    def parse_return(self) -> ReturnNode:
        token = self.expect(TokenType.KEMBALI)
        value = None
        if self.current_token().type not in (TokenType.NEWLINE, TokenType.EOF,
                                              TokenType.DEDENT, TokenType.SEMICOLON):
            value = self.parse_expression()
        self.skip_newlines()
        return ReturnNode(value=value, line=token.line, column=token.column)

    def parse_try(self) -> TryNode:
        token = self.expect(TokenType.CUBA)
        try_body = self.parse_block()

        except_clauses = []
        self.skip_newlines()

        while self.current_token().type == TokenType.TANGKAP:
            self.advance()
            exception_type = None
            exception_alias = None

            if self.current_token().type == TokenType.IDENTIFIER:
                exception_type = self.advance().value
                if self.current_token().type == TokenType.SEBAGAI:
                    self.advance()
                    exception_alias = self.expect(TokenType.IDENTIFIER).value

            except_body = self.parse_block()
            except_clauses.append((exception_type, exception_alias, except_body))
            self.skip_newlines()

        finally_body = None
        if self.current_token().type == TokenType.AKHIRNYA:
            self.advance()
            finally_body = self.parse_block()

        return TryNode(
            try_body=try_body, except_clauses=except_clauses,
            finally_body=finally_body, line=token.line, column=token.column
        )

    def parse_raise(self) -> RaiseNode:
        token = self.expect(TokenType.BANGKIT)
        exception = self.parse_expression()
        self.skip_newlines()
        return RaiseNode(exception=exception, line=token.line, column=token.column)

    def parse_import(self) -> ImportNode:
        token = self.expect(TokenType.IMPORT)
        # Module name can be dotted: import os.path
        module = self.expect(TokenType.IDENTIFIER).value
        while self.current_token().type == TokenType.DOT:
            self.advance()
            module += '.' + self.expect(TokenType.IDENTIFIER).value

        alias = None
        if self.current_token().type == TokenType.SEBAGAI:
            self.advance()
            alias = self.expect(TokenType.IDENTIFIER).value

        self.skip_newlines()
        return ImportNode(module=module, alias=alias, line=token.line, column=token.column)

    def parse_from_import(self) -> FromImportNode:
        token = self.expect(TokenType.DARI)
        module = self.expect(TokenType.IDENTIFIER).value
        while self.current_token().type == TokenType.DOT:
            self.advance()
            module += '.' + self.expect(TokenType.IDENTIFIER).value

        self.expect(TokenType.IMPORT)

        names = []
        aliases = []

        # Support parenthesised imports: from mod import (a, b, c)
        parens = self.current_token().type == TokenType.LPAREN
        if parens:
            self.advance()

        while True:
            name_token = self.expect(TokenType.IDENTIFIER)
            names.append(name_token.value)

            alias = None
            if self.current_token().type == TokenType.SEBAGAI:
                self.advance()
                alias = self.expect(TokenType.IDENTIFIER).value
            aliases.append(alias)

            if self.current_token().type != TokenType.COMMA:
                break
            self.advance()
            if parens and self.current_token().type == TokenType.RPAREN:
                break

        if parens:
            self.expect(TokenType.RPAREN)

        self.skip_newlines()
        return FromImportNode(module=module, names=names, aliases=aliases,
                              line=token.line, column=token.column)

    def parse_global(self) -> GlobalNode:
        token = self.expect(TokenType.GLOBAL)
        names = [self.expect(TokenType.IDENTIFIER).value]
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            names.append(self.expect(TokenType.IDENTIFIER).value)
        self.skip_newlines()
        return GlobalNode(names=names, line=token.line, column=token.column)

    def parse_nonlocal(self) -> NonlocalNode:
        token = self.expect(TokenType.NONLOKAL)
        names = [self.expect(TokenType.IDENTIFIER).value]
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            names.append(self.expect(TokenType.IDENTIFIER).value)
        self.skip_newlines()
        return NonlocalNode(names=names, line=token.line, column=token.column)

    def parse_delete(self) -> DeleteNode:
        token = self.expect(TokenType.PADAM)
        target = self.parse_expression()
        self.skip_newlines()
        return DeleteNode(target=target, line=token.line, column=token.column)

    # ------------------------------------------------------------------ #
    #  Expressions (operator precedence climbing)                          #
    # ------------------------------------------------------------------ #

    def parse_expression(self) -> ASTNode:
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.current_token().type == TokenType.ATAU_LOGIK:
            op_token = self.advance()
            right = self.parse_and()
            left = BinaryOpNode(left=left, operator='atau_logik', right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_not()
        while self.current_token().type == TokenType.DAN:
            op_token = self.advance()
            right = self.parse_not()
            left = BinaryOpNode(left=left, operator='dan', right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_not(self) -> ASTNode:
        if self.current_token().type == TokenType.BUKAN:
            op_token = self.advance()
            operand = self.parse_not()
            return UnaryOpNode(operator='bukan', operand=operand,
                               line=op_token.line, column=op_token.column)
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()

        CMP_TYPES = {
            TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT,
            TokenType.LE, TokenType.GE, TokenType.DALAM, TokenType.ADALAH,
        }
        while self.current_token().type in CMP_TYPES:
            op_token = self.advance()
            # Handle "bukan dalam" (not in) and "bukan adalah" (is not)
            if op_token.type == TokenType.DALAM and isinstance(
                    self.tokens[self.pos - 2] if self.pos >= 2 else None, Token):
                pass  # normal 'dalam'
            right = self.parse_addition()
            if op_token.type in (TokenType.EQ, TokenType.NE, TokenType.LT,
                                  TokenType.GT, TokenType.LE, TokenType.GE):
                operator = op_token.value
            elif op_token.type == TokenType.DALAM:
                operator = 'dalam'
            elif op_token.type == TokenType.ADALAH:
                operator = 'adalah'
            else:
                operator = op_token.value
            left = BinaryOpNode(left=left, operator=operator, right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiplication()
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplication()
            left = BinaryOpNode(left=left, operator=op_token.value, right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_multiplication(self) -> ASTNode:
        left = self.parse_power()
        while self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE,
                                             TokenType.FLOOR_DIV, TokenType.MODULO):
            op_token = self.advance()
            right = self.parse_power()
            left = BinaryOpNode(left=left, operator=op_token.value, right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_power(self) -> ASTNode:
        left = self.parse_unary()
        if self.current_token().type == TokenType.POWER:
            op_token = self.advance()
            right = self.parse_power()  # Right-associative
            return BinaryOpNode(left=left, operator=op_token.value, right=right,
                                line=op_token.line, column=op_token.column)
        return left

    def parse_unary(self) -> ASTNode:
        if self.current_token().type == TokenType.MINUS:
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(operator='-', operand=operand,
                               line=op_token.line, column=op_token.column)
        if self.current_token().type == TokenType.PLUS:
            self.advance()
            return self.parse_unary()
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        """Parse postfix ops: calls, indexing, attribute access"""
        expr = self.parse_primary()

        while True:
            token = self.current_token()

            if token.type == TokenType.LPAREN:
                # Function / method call
                self.advance()
                arguments, keyword_args = self._parse_call_args()
                self.expect(TokenType.RPAREN)

                # Determine function expression
                if isinstance(expr, IdentifierNode):
                    func = expr.name
                else:
                    func = expr
                expr = FunctionCallNode(function=func, arguments=arguments,
                                        keyword_args=keyword_args,
                                        line=token.line, column=token.column)

            elif token.type == TokenType.LBRACKET:
                # Indexing / slicing
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexNode(object=expr, index=index, line=token.line, column=token.column)

            elif token.type == TokenType.DOT:
                # Attribute access
                self.advance()
                attr_token = self.expect(TokenType.IDENTIFIER)
                expr = AttributeNode(object=expr, attribute=attr_token.value,
                                     line=token.line, column=token.column)
            else:
                break

        return expr

    def _parse_call_args(self):
        """Parse function call arguments, returning (positional_list, keyword_dict)."""
        arguments = []
        keyword_args = {}

        while self.current_token().type != TokenType.RPAREN:
            # Peek ahead: if we see IDENTIFIER followed by ASSIGN, it's a keyword arg
            if (self.current_token().type == TokenType.IDENTIFIER
                    and self.peek().type == TokenType.ASSIGN):
                kw_name = self.advance().value  # identifier
                self.advance()                  # =
                kw_value = self.parse_expression()
                keyword_args[kw_name] = kw_value
            else:
                arguments.append(self.parse_expression())

            if self.current_token().type == TokenType.COMMA:
                self.advance()
            else:
                break

        return arguments, keyword_args

    # ------------------------------------------------------------------ #
    #  Primary expressions                                                 #
    # ------------------------------------------------------------------ #

    def parse_primary(self) -> ASTNode:
        token = self.current_token()

        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(value=token.value, line=token.line, column=token.column)

        if token.type == TokenType.STRING:
            self.advance()
            # Consecutive string literals concatenation: "a" "b" -> "ab"
            value = token.value
            while self.current_token().type == TokenType.STRING:
                value += self.advance().value
            return StringNode(value=value, line=token.line, column=token.column)

        if token.type == TokenType.FSTRING:
            self.advance()
            return self.parse_fstring(token.value, token)

        if token.type == TokenType.BENAR:
            self.advance()
            return BooleanNode(value=True, line=token.line, column=token.column)

        if token.type == TokenType.SALAH:
            self.advance()
            return BooleanNode(value=False, line=token.line, column=token.column)

        if token.type == TokenType.TIADA:
            self.advance()
            return NoneNode(line=token.line, column=token.column)

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return IdentifierNode(name=token.value, line=token.line, column=token.column)

        if token.type == TokenType.LBRACKET:
            return self.parse_list()

        if token.type == TokenType.LBRACE:
            return self.parse_dict()

        if token.type == TokenType.LPAREN:
            self.advance()
            # Empty tuple / parenthesised expr
            if self.current_token().type == TokenType.RPAREN:
                self.advance()
                return ListNode(elements=[], line=token.line, column=token.column)
            expr = self.parse_expression()
            # Check for tuple: (a, b, c)
            if self.current_token().type == TokenType.COMMA:
                elements = [expr]
                while self.current_token().type == TokenType.COMMA:
                    self.advance()
                    if self.current_token().type == TokenType.RPAREN:
                        break
                    elements.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return ListNode(elements=elements, line=token.line, column=token.column)
            self.expect(TokenType.RPAREN)
            return expr

        self.error(f"Token tidak dijangka: {token.type.name} ({token.value!r})")

    def parse_list(self) -> ListNode:
        token = self.expect(TokenType.LBRACKET)
        elements = []
        self.skip_newlines()
        while self.current_token().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            self.skip_newlines()
            if self.current_token().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
            else:
                break
        self.expect(TokenType.RBRACKET)
        return ListNode(elements=elements, line=token.line, column=token.column)

    def parse_dict(self) -> DictNode:
        token = self.expect(TokenType.LBRACE)
        pairs = []
        self.skip_newlines()
        while self.current_token().type != TokenType.RBRACE:
            key = self.parse_expression()
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            pairs.append((key, value))
            self.skip_newlines()
            if self.current_token().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
            else:
                break
        self.expect(TokenType.RBRACE)
        return DictNode(pairs=pairs, line=token.line, column=token.column)

    # ------------------------------------------------------------------ #
    #  F-string parsing                                                    #
    # ------------------------------------------------------------------ #

    def parse_fstring(self, raw: str, token: Token) -> FStringNode:
        """Parse a raw f-string content into alternating literal/expression parts."""
        parts = []
        i = 0
        current_literal = ''

        while i < len(raw):
            ch = raw[i]

            # Escaped braces: {{ -> { and }} -> }
            if ch == '{' and i + 1 < len(raw) and raw[i + 1] == '{':
                current_literal += '{'
                i += 2
                continue
            if ch == '}' and i + 1 < len(raw) and raw[i + 1] == '}':
                current_literal += '}'
                i += 2
                continue

            if ch == '{':
                # Save pending literal
                if current_literal:
                    parts.append(StringNode(value=current_literal,
                                            line=token.line, column=token.column))
                    current_literal = ''

                # Find matching closing brace (handle nested braces)
                i += 1
                depth = 1
                expr_chars = []
                while i < len(raw) and depth > 0:
                    if raw[i] == '{':
                        depth += 1
                    elif raw[i] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    expr_chars.append(raw[i])
                    i += 1

                if depth != 0:
                    raise SyntaxError(f"f-string tidak sah: kurungan pendakap tidak ditutup")

                expr_str = ''.join(expr_chars)
                i += 1  # skip closing }

                # Strip format spec after ':' (e.g., {x:.2f} -> parse only {x})
                # Simple approach: if there's a colon not inside brackets, split
                fmt_spec = ''
                colon_pos = self._find_format_colon(expr_str)
                if colon_pos is not None:
                    fmt_spec = expr_str[colon_pos + 1:]
                    expr_str = expr_str[:colon_pos]

                expr_str = expr_str.strip()
                if expr_str:
                    # Parse the expression using a sub-lexer/parser
                    sub_node = self._parse_inline_expr(expr_str, token)
                    parts.append(sub_node)

            else:
                # Handle escape sequences in the literal portion
                if ch == '\\' and i + 1 < len(raw):
                    esc = raw[i + 1]
                    escape_map = {
                        'n': '\n', 't': '\t', 'r': '\r',
                        '\\': '\\', '"': '"', "'": "'",
                    }
                    current_literal += escape_map.get(esc, esc)
                    i += 2
                else:
                    current_literal += ch
                    i += 1

        if current_literal:
            parts.append(StringNode(value=current_literal, line=token.line, column=token.column))

        return FStringNode(parts=parts, line=token.line, column=token.column)

    def _find_format_colon(self, expr_str: str) -> Optional[int]:
        """Find the position of a format-spec colon not inside brackets/quotes."""
        depth = 0
        for i, ch in enumerate(expr_str):
            if ch in ('(', '[', '{'):
                depth += 1
            elif ch in (')', ']', '}'):
                depth -= 1
            elif ch == ':' and depth == 0:
                return i
        return None

    def _parse_inline_expr(self, expr_str: str, parent_token: Token) -> ASTNode:
        """Lex and parse a small expression string (used inside f-strings)."""
        from kilat_lexer2 import KilatLexer2
        try:
            lexer = KilatLexer2(expr_str)
            tokens = lexer.tokenize()
            sub_parser = KilatParser(tokens)
            return sub_parser.parse_expression()
        except Exception as e:
            raise SyntaxError(
                f"Ralat dalam ekspresi f-string {expr_str!r} "
                f"di baris {parent_token.line}: {e}"
            )


# ------------------------------------------------------------------ #
#  Convenience function                                                #
# ------------------------------------------------------------------ #

def parse_kilat(source: str) -> ProgramNode:
    """Lex and parse Kilat-Lang source code, returning the AST."""
    lexer = KilatLexer2(source)
    tokens = lexer.tokenize()
    parser = KilatParser(tokens)
    return parser.parse()
