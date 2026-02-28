"""
Kilat-Lang Bytecode Compiler
Compiles AST nodes into bytecode (CodeObject) for the Kilat VM.
"""

from kilat_ast import *
from kilat_bytecode import OpCode, CodeObject


class CompileError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        super().__init__(message)


class KilatBytecodeCompiler:
    """Compiles a Kilat AST into a CodeObject."""

    def __init__(self, name: str = '<module>'):
        self.code = CodeObject(name)
        self._loop_stack = []  # stack of (loop_type, start_addr, break_patches)
        self._globals = set()  # names declared global in current scope

    # ---------------------------------------------------------------- #
    #  Public API                                                       #
    # ---------------------------------------------------------------- #

    def compile_program(self, program: ProgramNode) -> CodeObject:
        for stmt in program.statements:
            self.compile_node(stmt)
            # If statement leaves a value on stack (expression statement), pop it
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP, line=getattr(stmt, 'line', 0))
        return self.code

    # ---------------------------------------------------------------- #
    #  Node dispatcher                                                  #
    # ---------------------------------------------------------------- #

    def compile_node(self, node: ASTNode):
        """Compile a single AST node."""
        method_name = '_compile_' + type(node).__name__
        method = getattr(self, method_name, None)
        if method is None:
            raise CompileError(
                f"Cannot compile node type: {type(node).__name__}",
                getattr(node, 'line', 0), getattr(node, 'column', 0)
            )
        method(node)

    # ---------------------------------------------------------------- #
    #  Literals                                                         #
    # ---------------------------------------------------------------- #

    def _compile_NumberNode(self, node: NumberNode):
        idx = self.code.add_constant(node.value)
        self.code.emit(OpCode.LOAD_CONST, idx, node.line)

    def _compile_StringNode(self, node: StringNode):
        idx = self.code.add_constant(node.value)
        self.code.emit(OpCode.LOAD_CONST, idx, node.line)

    def _compile_BooleanNode(self, node: BooleanNode):
        idx = self.code.add_constant(node.value)
        self.code.emit(OpCode.LOAD_CONST, idx, node.line)

    def _compile_NoneNode(self, node: NoneNode):
        idx = self.code.add_constant(None)
        self.code.emit(OpCode.LOAD_CONST, idx, node.line)

    def _compile_IdentifierNode(self, node: IdentifierNode):
        name_idx = self.code.add_name(node.name)
        if node.name in self._globals:
            self.code.emit(OpCode.LOAD_GLOBAL, name_idx, node.line)
        else:
            self.code.emit(OpCode.LOAD_NAME, name_idx, node.line)

    # ---------------------------------------------------------------- #
    #  Collections                                                      #
    # ---------------------------------------------------------------- #

    def _compile_ListNode(self, node: ListNode):
        for elem in node.elements:
            self.compile_node(elem)
        self.code.emit(OpCode.BUILD_LIST, len(node.elements), node.line)

    def _compile_TupleNode(self, node: TupleNode):
        for elem in node.elements:
            self.compile_node(elem)
        self.code.emit(OpCode.BUILD_TUPLE, len(node.elements), node.line)

    def _compile_DictNode(self, node: DictNode):
        for key_node, val_node in node.pairs:
            self.compile_node(key_node)
            self.compile_node(val_node)
        self.code.emit(OpCode.BUILD_DICT, len(node.pairs), node.line)

    def _compile_FStringNode(self, node: FStringNode):
        for part in node.parts:
            self.compile_node(part)
        self.code.emit(OpCode.BUILD_FSTRING, len(node.parts), node.line)

    def _compile_SliceNode(self, node: SliceNode):
        # Push start, stop, step (using None for omitted parts)
        for part in (node.start, node.stop, node.step):
            if part is not None:
                self.compile_node(part)
            else:
                idx = self.code.add_constant(None)
                self.code.emit(OpCode.LOAD_CONST, idx, node.line)
        self.code.emit(OpCode.BUILD_SLICE, 3, node.line)

    # ---------------------------------------------------------------- #
    #  Operations                                                       #
    # ---------------------------------------------------------------- #

    def _compile_BinaryOpNode(self, node: BinaryOpNode):
        op = node.operator

        # Short-circuit logical operators
        if op == 'dan':
            self.compile_node(node.left)
            jump_idx = self.code.emit(OpCode.JUMP_IF_FALSE_OR_POP, 0, node.line)
            self.compile_node(node.right)
            self.code.patch_jump(jump_idx)
            return

        if op == 'atau_logik':
            self.compile_node(node.left)
            jump_idx = self.code.emit(OpCode.JUMP_IF_TRUE_OR_POP, 0, node.line)
            self.compile_node(node.right)
            self.code.patch_jump(jump_idx)
            return

        # Normal binary ops: evaluate both sides
        self.compile_node(node.left)
        self.compile_node(node.right)

        op_map = {
            '+': OpCode.BINARY_ADD,
            '-': OpCode.BINARY_SUB,
            '*': OpCode.BINARY_MUL,
            '/': OpCode.BINARY_DIV,
            '//': OpCode.BINARY_FLOOR_DIV,
            '%': OpCode.BINARY_MOD,
            '**': OpCode.BINARY_POW,
            '==': OpCode.COMPARE_EQ,
            '!=': OpCode.COMPARE_NE,
            '<': OpCode.COMPARE_LT,
            '>': OpCode.COMPARE_GT,
            '<=': OpCode.COMPARE_LE,
            '>=': OpCode.COMPARE_GE,
            'dalam': OpCode.COMPARE_IN,
            'adalah': OpCode.COMPARE_IS,
        }

        if op in op_map:
            self.code.emit(op_map[op], line=node.line)
        else:
            raise CompileError(f"Unknown operator: {op}", node.line, node.column)

    def _compile_UnaryOpNode(self, node: UnaryOpNode):
        self.compile_node(node.operand)
        if node.operator == '-':
            self.code.emit(OpCode.UNARY_NEG, line=node.line)
        elif node.operator == '+':
            self.code.emit(OpCode.UNARY_POS, line=node.line)
        elif node.operator == 'bukan':
            self.code.emit(OpCode.UNARY_NOT, line=node.line)
        else:
            raise CompileError(f"Unknown unary operator: {node.operator}",
                               node.line, node.column)

    # ---------------------------------------------------------------- #
    #  Assignment                                                       #
    # ---------------------------------------------------------------- #

    def _compile_AssignmentNode(self, node: AssignmentNode):
        self.compile_node(node.value)
        name_idx = self.code.add_name(node.target)
        if node.target in self._globals:
            self.code.emit(OpCode.STORE_GLOBAL, name_idx, node.line)
        else:
            # Regular assignment always defines in current scope
            self.code.emit(OpCode.STORE_NAME_DEFINE, name_idx, node.line)

    def _compile_AugmentedAssignmentNode(self, node: AugmentedAssignmentNode):
        self.compile_node(node.value)
        name_idx = self.code.add_name(node.target)
        aug_map = {
            '+': OpCode.AUG_ADD,
            '-': OpCode.AUG_SUB,
            '*': OpCode.AUG_MUL,
            '/': OpCode.AUG_DIV,
            '//': OpCode.AUG_FLOOR_DIV,
            '**': OpCode.AUG_POW,
            '%': OpCode.AUG_MOD,
        }
        if node.operator in aug_map:
            self.code.emit(aug_map[node.operator], name_idx, node.line)
        else:
            raise CompileError(f"Unknown augmented operator: {node.operator}",
                               node.line, node.column)

    def _compile_IndexAssignmentNode(self, node: IndexAssignmentNode):
        self.compile_node(node.object)
        self.compile_node(node.index)
        self.compile_node(node.value)
        self.code.emit(OpCode.STORE_INDEX, line=node.line)

    def _compile_AttributeAssignmentNode(self, node: AttributeAssignmentNode):
        self.compile_node(node.object)
        self.compile_node(node.value)
        attr_idx = self.code.add_name(node.attribute)
        self.code.emit(OpCode.STORE_ATTR, attr_idx, node.line)

    # ---------------------------------------------------------------- #
    #  Attribute / Index access                                         #
    # ---------------------------------------------------------------- #

    def _compile_AttributeNode(self, node: AttributeNode):
        self.compile_node(node.object)
        attr_idx = self.code.add_name(node.attribute)
        self.code.emit(OpCode.LOAD_ATTR, attr_idx, node.line)

    def _compile_IndexNode(self, node: IndexNode):
        self.compile_node(node.object)
        self.compile_node(node.index)
        self.code.emit(OpCode.LOAD_INDEX, line=node.line)

    # ---------------------------------------------------------------- #
    #  Control flow                                                     #
    # ---------------------------------------------------------------- #

    def _compile_IfNode(self, node: IfNode):
        end_jumps = []

        # Main if
        self.compile_node(node.condition)
        false_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)

        for stmt in node.then_body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        end_jumps.append(self.code.emit(OpCode.JUMP_ABSOLUTE, 0, node.line))
        self.code.patch_jump(false_jump)

        # Elif parts
        for elif_cond, elif_body in node.elif_parts:
            self.compile_node(elif_cond)
            elif_false = self.code.emit(OpCode.JUMP_IF_FALSE, 0, getattr(elif_cond, 'line', 0))

            for stmt in elif_body:
                self.compile_node(stmt)
                if self._is_expression(stmt):
                    self.code.emit(OpCode.POP_TOP)

            end_jumps.append(self.code.emit(OpCode.JUMP_ABSOLUTE, 0))
            self.code.patch_jump(elif_false)

        # Else
        if node.else_body:
            for stmt in node.else_body:
                self.compile_node(stmt)
                if self._is_expression(stmt):
                    self.code.emit(OpCode.POP_TOP)

        # Patch all end jumps
        end_target = self.code.current_offset()
        for j in end_jumps:
            self.code.patch_jump(j, end_target)

    def _compile_WhileNode(self, node: WhileNode):
        loop_start = self.code.current_offset()
        break_patches = []

        self._loop_stack.append(('while', loop_start, break_patches))

        self.compile_node(node.condition)
        exit_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)

        for stmt in node.body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        self.code.emit(OpCode.JUMP_ABSOLUTE, loop_start, node.line)
        self.code.patch_jump(exit_jump)

        self._loop_stack.pop()

        # Patch break jumps
        end_target = self.code.current_offset()
        for bp in break_patches:
            self.code.patch_jump(bp, end_target)

    def _compile_BreakNode(self, node: BreakNode):
        if not self._loop_stack:
            raise CompileError("'berhenti' di luar gelung", node.line, node.column)
        loop_type, _, break_patches = self._loop_stack[-1]
        # In a for loop, pop the iterator off the stack before jumping
        if loop_type == 'for':
            self.code.emit(OpCode.POP_TOP, line=node.line)
        bp = self.code.emit(OpCode.JUMP_ABSOLUTE, 0, node.line)
        break_patches.append(bp)

    def _compile_ContinueNode(self, node: ContinueNode):
        if not self._loop_stack:
            raise CompileError("'teruskan' di luar gelung", node.line, node.column)
        _, loop_start, _ = self._loop_stack[-1]
        self.code.emit(OpCode.JUMP_ABSOLUTE, loop_start, node.line)

    def _compile_ReturnNode(self, node: ReturnNode):
        if node.value is not None:
            self.compile_node(node.value)
        else:
            idx = self.code.add_constant(None)
            self.code.emit(OpCode.LOAD_CONST, idx, node.line)
        self.code.emit(OpCode.RETURN_VALUE, line=node.line)

    # ---------------------------------------------------------------- #
    #  Function calls                                                   #
    # ---------------------------------------------------------------- #

    def _compile_FunctionCallNode(self, node: FunctionCallNode):
        # Compile the function expression
        if isinstance(node.function, str):
            name_idx = self.code.add_name(node.function)
            if node.function in self._globals:
                self.code.emit(OpCode.LOAD_GLOBAL, name_idx, node.line)
            else:
                self.code.emit(OpCode.LOAD_NAME, name_idx, node.line)
        else:
            self.compile_node(node.function)

        # Compile positional arguments
        for arg in node.arguments:
            self.compile_node(arg)

        if node.keyword_args:
            # Compile keyword argument values
            for kw_val in node.keyword_args.values():
                self.compile_node(kw_val)
            # Push keyword names as a constant tuple
            kw_names = list(node.keyword_args.keys())
            kw_idx = self.code.add_constant(kw_names)
            self.code.emit(OpCode.LOAD_CONST, kw_idx, node.line)
            # CALL_FUNCTION_KW: arg = number of positional args
            # Stack: func, pos_args..., kw_values..., kw_names_tuple
            self.code.emit(OpCode.CALL_FUNCTION_KW, len(node.arguments), node.line)
        else:
            self.code.emit(OpCode.CALL_FUNCTION, len(node.arguments), node.line)

    # ---------------------------------------------------------------- #
    #  Exception handling                                               #
    # ---------------------------------------------------------------- #

    def _compile_TryNode(self, node: TryNode):
        # SETUP_TRY: arg = address of first handler
        setup_idx = self.code.emit(OpCode.SETUP_TRY, 0, node.line)

        # Compile try body
        for stmt in node.try_body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        self.code.emit(OpCode.POP_TRY, line=node.line)

        # Jump past handlers
        end_jump = self.code.emit(OpCode.JUMP_ABSOLUTE, 0, node.line)

        # Patch SETUP_TRY to point here (handler start)
        self.code.patch_jump(setup_idx)

        # Compile exception handlers
        handler_end_jumps = []
        for i, (exc_type, exc_alias, exc_body) in enumerate(node.except_clauses):
            # MATCH_EXCEPTION: check if current exception matches
            if exc_type is not None:
                type_name_idx = self.code.add_name(exc_type)
                self.code.emit(OpCode.MATCH_EXCEPTION, type_name_idx, node.line)
            else:
                self.code.emit(OpCode.MATCH_EXCEPTION, -1, node.line)

            # If no match, jump to next handler
            no_match = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)

            # Bind exception to alias if provided
            if exc_alias:
                alias_idx = self.code.add_name(exc_alias)
                # The exception value is available via a special load
                self.code.emit(OpCode.LOAD_CONST, self.code.add_constant('__exception__'), node.line)
                self.code.emit(OpCode.STORE_NAME_DEFINE, alias_idx, node.line)

            # Compile handler body
            for stmt in exc_body:
                self.compile_node(stmt)
                if self._is_expression(stmt):
                    self.code.emit(OpCode.POP_TOP)

            handler_end_jumps.append(self.code.emit(OpCode.JUMP_ABSOLUTE, 0, node.line))
            self.code.patch_jump(no_match)

        # If no handler matched, re-raise
        self.code.emit(OpCode.END_FINALLY, line=node.line)

        # Patch all handler end jumps and the main end jump
        finally_start = self.code.current_offset()

        # Compile finally body if present
        if node.finally_body:
            for stmt in node.finally_body:
                self.compile_node(stmt)
                if self._is_expression(stmt):
                    self.code.emit(OpCode.POP_TOP)

        end_target = self.code.current_offset()

        # Patch jumps
        self.code.patch_jump(end_jump, finally_start if node.finally_body else end_target)
        for j in handler_end_jumps:
            self.code.patch_jump(j, finally_start if node.finally_body else end_target)

    def _compile_RaiseNode(self, node: RaiseNode):
        self.compile_node(node.exception)
        self.code.emit(OpCode.RAISE, line=node.line)

    # ---------------------------------------------------------------- #
    #  Imports                                                          #
    # ---------------------------------------------------------------- #

    def _compile_ImportNode(self, node: ImportNode):
        mod_idx = self.code.add_name(node.module)
        self.code.emit(OpCode.IMPORT_MODULE, mod_idx, node.line)
        # Store with alias or module name
        alias = node.alias or node.module.split('.')[-1]
        alias_idx = self.code.add_name(alias)
        self.code.emit(OpCode.STORE_NAME_DEFINE, alias_idx, node.line)

    def _compile_FromImportNode(self, node: FromImportNode):
        mod_idx = self.code.add_name(node.module)
        self.code.emit(OpCode.IMPORT_MODULE, mod_idx, node.line)
        for name, alias in zip(node.names, node.aliases):
            self.code.emit(OpCode.DUP_TOP, line=node.line)
            name_idx = self.code.add_name(name)
            self.code.emit(OpCode.IMPORT_FROM, name_idx, node.line)
            store_name = alias or name
            store_idx = self.code.add_name(store_name)
            self.code.emit(OpCode.STORE_NAME_DEFINE, store_idx, node.line)
        self.code.emit(OpCode.POP_TOP, line=node.line)

    # ---------------------------------------------------------------- #
    #  Scope                                                            #
    # ---------------------------------------------------------------- #

    def _compile_GlobalNode(self, node: GlobalNode):
        for name in node.names:
            self._globals.add(name)
            name_idx = self.code.add_name(name)
            self.code.emit(OpCode.DECLARE_GLOBAL, name_idx, node.line)

    def _compile_NonlocalNode(self, node: NonlocalNode):
        # Nonlocal is handled at runtime by Environment.set()
        pass

    # ---------------------------------------------------------------- #
    #  Delete / Pass                                                    #
    # ---------------------------------------------------------------- #

    def _compile_DeleteNode(self, node: DeleteNode):
        target = node.target
        if isinstance(target, IdentifierNode):
            name_idx = self.code.add_name(target.name)
            self.code.emit(OpCode.DELETE_NAME, name_idx, node.line)
        elif isinstance(target, IndexNode):
            self.compile_node(target.object)
            self.compile_node(target.index)
            self.code.emit(OpCode.DELETE_INDEX, line=node.line)

    def _compile_PassNode(self, node: PassNode):
        self.code.emit(OpCode.NOP, line=node.line)

    # ---------------------------------------------------------------- #
    #  List comprehension                                               #
    # ---------------------------------------------------------------- #

    def _compile_ListCompNode(self, node: ListCompNode):
        # Build an empty list, iterate, append matching items
        self.code.emit(OpCode.BUILD_LIST, 0, node.line)  # result = []

        # Compile iterable and get iterator
        self.compile_node(node.iterable)
        self.code.emit(OpCode.GET_ITER, line=node.line)

        loop_start = self.code.current_offset()
        iter_jump = self.code.emit(OpCode.FOR_ITER, 0, node.line)

        # Store loop variable(s)
        if node.variables:
            self.code.emit(OpCode.UNPACK_SEQUENCE, len(node.variables), node.line)
            for var in node.variables:
                name_idx = self.code.add_name(var)
                self.code.emit(OpCode.STORE_NAME, name_idx, node.line)
        else:
            name_idx = self.code.add_name(node.variable)
            self.code.emit(OpCode.STORE_NAME, name_idx, node.line)

        # Optional condition
        skip_jump = None
        if node.condition is not None:
            self.compile_node(node.condition)
            skip_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)

        # Compile expression and append to result list
        # Stack: [result_list, ...] — we need to dup the list ref, compile expr, append
        # Use ROT to get list to top, then use LOAD_ATTR 'append' + call
        # Simpler approach: use a temporary variable for the result list
        # Actually, the result list is at the bottom of the stack.
        # Let's use a different approach: compile into a loop that builds the list

        # The result list is deep in the stack. We'll load it by name.
        result_name = f'__listcomp_{id(node)}__'
        result_idx = self.code.add_name(result_name)

        # At the start (before loop), we stored the empty list. Let's save it to a temp name.
        # We need to restructure: save list first, then iterate.
        # Let me redo this approach...

        # Actually, let me use a simpler approach:
        # Before the loop, store the empty list in a temp var
        # In the loop body, load the temp var, compile expr, call append
        # After the loop, load the temp var as the result

        # Rewrite: undo what we emitted and start over
        # Since we can't easily undo, let me restructure the method

        # Load the result list (it's at the bottom of the stack before the iterator)
        # Stack state: [..., result_list, iterator]
        # We need to get result_list to append to it.
        # Simplest: store result list in a temp var before the loop.

        pass  # handled below

        # Skip the append if condition failed
        if skip_jump is not None:
            self.code.patch_jump(skip_jump)

        self.code.emit(OpCode.JUMP_ABSOLUTE, loop_start, node.line)
        self.code.patch_jump(iter_jump)

        # Load result — but we have a problem with the stack approach.
        # Let me completely redo this method with a cleaner approach.

    # Override the above with a clean implementation
    def _compile_ListCompNode(self, node: ListCompNode):
        """Compile list comprehension: [expr for var in iterable if cond]"""
        # Use a temporary name to accumulate results
        temp_name = f'__lc_{self.code.current_offset()}__'
        temp_idx = self.code.add_name(temp_name)

        # Create empty result list and store
        self.code.emit(OpCode.BUILD_LIST, 0, node.line)
        self.code.emit(OpCode.STORE_NAME, temp_idx, node.line)

        # Compile iterable and get iterator
        self.compile_node(node.iterable)
        self.code.emit(OpCode.GET_ITER, line=node.line)

        loop_start = self.code.current_offset()
        iter_jump = self.code.emit(OpCode.FOR_ITER, 0, node.line)

        # Store loop variable(s)
        if node.variables:
            self.code.emit(OpCode.UNPACK_SEQUENCE, len(node.variables), node.line)
            for var in node.variables:
                vidx = self.code.add_name(var)
                self.code.emit(OpCode.STORE_NAME, vidx, node.line)
        else:
            vidx = self.code.add_name(node.variable)
            self.code.emit(OpCode.STORE_NAME, vidx, node.line)

        # Optional condition
        skip_jump = None
        if node.condition is not None:
            self.compile_node(node.condition)
            skip_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)

        # Load result list, compile expression, append
        self.code.emit(OpCode.LOAD_NAME, temp_idx, node.line)
        self.compile_node(node.expression)
        # Call list.append(value): LOAD_ATTR 'append', then swap, then CALL_FUNCTION
        append_idx = self.code.add_name('append')
        self.code.emit(OpCode.ROT_TWO, line=node.line)  # [value, list] -> [list, value]
        self.code.emit(OpCode.LOAD_ATTR, append_idx, node.line)
        self.code.emit(OpCode.ROT_TWO, line=node.line)  # [value, append] -> [append, value]
        self.code.emit(OpCode.CALL_FUNCTION, 1, node.line)
        self.code.emit(OpCode.POP_TOP, line=node.line)  # discard None return from append

        if skip_jump is not None:
            self.code.patch_jump(skip_jump)

        self.code.emit(OpCode.JUMP_ABSOLUTE, loop_start, node.line)
        self.code.patch_jump(iter_jump)

        # Load result list as the expression value
        self.code.emit(OpCode.LOAD_NAME, temp_idx, node.line)

    # ---------------------------------------------------------------- #
    #  Lambda                                                           #
    # ---------------------------------------------------------------- #

    def _compile_LambdaNode(self, node: LambdaNode):
        # Compile lambda body into a nested CodeObject
        func_compiler = KilatBytecodeCompiler(name='<lambda>')
        func_compiler.code.param_count = len(node.parameters)
        func_compiler.code.param_names = list(node.parameters)

        # Lambda body is a single expression — compile and return it
        func_compiler.compile_node(node.body)
        func_compiler.code.emit(OpCode.RETURN_VALUE, line=node.line)

        # Push default values
        for default in node.defaults:
            self.compile_node(default)

        # Push the code object
        code_idx = self.code.add_constant(func_compiler.code)
        self.code.emit(OpCode.LOAD_CONST, code_idx, node.line)
        self.code.emit(OpCode.MAKE_FUNCTION, len(node.defaults), node.line)

    # ---------------------------------------------------------------- #
    #  Ternary expression                                               #
    # ---------------------------------------------------------------- #

    def _compile_TernaryNode(self, node: TernaryNode):
        # Compile: true_value jika condition atau false_value
        self.compile_node(node.condition)
        false_jump = self.code.emit(OpCode.JUMP_IF_FALSE, 0, node.line)
        self.compile_node(node.true_value)
        end_jump = self.code.emit(OpCode.JUMP_ABSOLUTE, 0, node.line)
        self.code.patch_jump(false_jump)
        self.compile_node(node.false_value)
        self.code.patch_jump(end_jump)

    # ---------------------------------------------------------------- #
    #  Multi-assignment                                                 #
    # ---------------------------------------------------------------- #

    def _compile_MultiAssignmentNode(self, node: MultiAssignmentNode):
        self.compile_node(node.value)
        self.code.emit(OpCode.UNPACK_SEQUENCE, len(node.targets), node.line)
        for target in node.targets:
            name_idx = self.code.add_name(target)
            if target in self._globals:
                self.code.emit(OpCode.STORE_GLOBAL, name_idx, node.line)
            else:
                self.code.emit(OpCode.STORE_NAME_DEFINE, name_idx, node.line)

    # ---------------------------------------------------------------- #
    #  With statement                                                   #
    # ---------------------------------------------------------------- #

    def _compile_WithNode(self, node: WithNode):
        # Compile context expression
        self.compile_node(node.context_expr)

        # Call __enter__
        enter_idx = self.code.add_name('__enter__')
        self.code.emit(OpCode.DUP_TOP, line=node.line)  # keep context for __exit__
        self.code.emit(OpCode.LOAD_ATTR, enter_idx, node.line)
        self.code.emit(OpCode.CALL_FUNCTION, 0, node.line)

        # Store alias if present
        if node.alias:
            alias_idx = self.code.add_name(node.alias)
            self.code.emit(OpCode.STORE_NAME_DEFINE, alias_idx, node.line)
        else:
            self.code.emit(OpCode.POP_TOP, line=node.line)

        # Store context manager in temp for __exit__
        ctx_name = f'__ctx_{self.code.current_offset()}__'
        ctx_idx = self.code.add_name(ctx_name)
        # The context is still on stack from DUP_TOP; but we called __enter__ on it.
        # Actually we need to restructure. Let's save context first.

        # Simplified approach: save context to temp, then call __enter__
        # Re-emit properly:

        # Clear previous emissions and redo
        # Since we can't easily undo, let's use a simpler approach for with:
        # Just compile the body and call __exit__ in a try/finally pattern

        # Compile body
        for stmt in node.body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        # Call __exit__(None, None, None) — simplified, no exception handling
        exit_idx = self.code.add_name('__exit__')
        self.code.emit(OpCode.LOAD_ATTR, exit_idx, node.line)
        none_idx = self.code.add_constant(None)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.CALL_FUNCTION, 3, node.line)
        self.code.emit(OpCode.POP_TOP, line=node.line)

    # Override with clean implementation
    def _compile_WithNode(self, node: WithNode):
        """Compile with statement using temp variables."""
        ctx_name = f'__ctx_{self.code.current_offset()}__'
        ctx_idx = self.code.add_name(ctx_name)

        # Compile context expr and save to temp
        self.compile_node(node.context_expr)
        self.code.emit(OpCode.DUP_TOP, line=node.line)
        self.code.emit(OpCode.STORE_NAME, ctx_idx, node.line)

        # Call __enter__
        enter_idx = self.code.add_name('__enter__')
        self.code.emit(OpCode.LOAD_ATTR, enter_idx, node.line)
        self.code.emit(OpCode.CALL_FUNCTION, 0, node.line)

        if node.alias:
            alias_idx = self.code.add_name(node.alias)
            self.code.emit(OpCode.STORE_NAME_DEFINE, alias_idx, node.line)
        else:
            self.code.emit(OpCode.POP_TOP, line=node.line)

        # Compile body
        for stmt in node.body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        # Call __exit__(None, None, None)
        self.code.emit(OpCode.LOAD_NAME, ctx_idx, node.line)
        exit_idx = self.code.add_name('__exit__')
        self.code.emit(OpCode.LOAD_ATTR, exit_idx, node.line)
        none_idx = self.code.add_constant(None)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)
        self.code.emit(OpCode.CALL_FUNCTION, 3, node.line)
        self.code.emit(OpCode.POP_TOP, line=node.line)

    # ---------------------------------------------------------------- #
    #  Yield (not fully supported in bytecode mode)                     #
    # ---------------------------------------------------------------- #

    def _compile_YieldNode(self, node: YieldNode):
        raise CompileError(
            "berikan (yield) belum disokong dalam mod kod bait",
            node.line, node.column
        )

    # ---------------------------------------------------------------- #
    #  For loop with tuple unpacking                                    #
    # ---------------------------------------------------------------- #

    def _compile_ForNode(self, node: ForNode):
        # Compile iterable and get iterator
        self.compile_node(node.iterable)
        self.code.emit(OpCode.GET_ITER, line=node.line)

        loop_start = self.code.current_offset()
        break_patches = []
        self._loop_stack.append(('for', loop_start, break_patches))

        iter_jump = self.code.emit(OpCode.FOR_ITER, 0, node.line)

        # Store loop variable(s)
        if node.variables:
            self.code.emit(OpCode.UNPACK_SEQUENCE, len(node.variables), node.line)
            for var in node.variables:
                name_idx = self.code.add_name(var)
                self.code.emit(OpCode.STORE_NAME, name_idx, node.line)
        else:
            name_idx = self.code.add_name(node.variable)
            self.code.emit(OpCode.STORE_NAME, name_idx, node.line)

        # Body
        for stmt in node.body:
            self.compile_node(stmt)
            if self._is_expression(stmt):
                self.code.emit(OpCode.POP_TOP)

        self.code.emit(OpCode.JUMP_ABSOLUTE, loop_start, node.line)
        self.code.patch_jump(iter_jump)

        self._loop_stack.pop()

        end_target = self.code.current_offset()
        for bp in break_patches:
            self.code.patch_jump(bp, end_target)

    # ---------------------------------------------------------------- #
    #  Functions with decorators, *args, **kwargs                       #
    # ---------------------------------------------------------------- #

    def _compile_FunctionDefNode(self, node: FunctionDefNode):
        # Compile the function body into a nested CodeObject
        func_compiler = KilatBytecodeCompiler(name=node.name)
        func_compiler.code.param_count = len(node.parameters)
        func_compiler.code.param_names = list(node.parameters)
        # Store var_args/kw_args info in the code object for the VM
        func_compiler.code.var_args = getattr(node, 'var_args', None)
        func_compiler.code.kw_args = getattr(node, 'kw_args', None)

        for stmt in node.body:
            func_compiler.compile_node(stmt)
            if func_compiler._is_expression(stmt):
                func_compiler.code.emit(OpCode.POP_TOP)

        none_idx = func_compiler.code.add_constant(None)
        func_compiler.code.emit(OpCode.LOAD_CONST, none_idx)
        func_compiler.code.emit(OpCode.RETURN_VALUE)

        # Push default values on stack
        for default in node.defaults:
            self.compile_node(default)

        # Push the code object as a constant
        code_idx = self.code.add_constant(func_compiler.code)
        self.code.emit(OpCode.LOAD_CONST, code_idx, node.line)

        self.code.emit(OpCode.MAKE_FUNCTION, len(node.defaults), node.line)

        # Apply decorators (in reverse order): each decorator wraps the function
        for decorator_node in reversed(node.decorators):
            self.compile_node(decorator_node)
            self.code.emit(OpCode.ROT_TWO, line=node.line)
            self.code.emit(OpCode.CALL_FUNCTION, 1, node.line)

        # Store the function
        name_idx = self.code.add_name(node.name)
        self.code.emit(OpCode.STORE_NAME_DEFINE, name_idx, node.line)

    # ---------------------------------------------------------------- #
    #  Classes with decorators                                          #
    # ---------------------------------------------------------------- #

    def _compile_ClassDefNode(self, node: ClassDefNode):
        # Push base class name (or None)
        if node.base_class:
            base_idx = self.code.add_name(node.base_class)
            self.code.emit(OpCode.LOAD_NAME, base_idx, node.line)
        else:
            none_idx = self.code.add_constant(None)
            self.code.emit(OpCode.LOAD_CONST, none_idx, node.line)

        # Compile each method
        method_names = []
        for stmt in node.body:
            if isinstance(stmt, FunctionDefNode):
                method_compiler = KilatBytecodeCompiler(name=stmt.name)
                method_compiler.code.param_count = len(stmt.parameters)
                method_compiler.code.param_names = list(stmt.parameters)
                method_compiler.code.var_args = getattr(stmt, 'var_args', None)
                method_compiler.code.kw_args = getattr(stmt, 'kw_args', None)

                for s in stmt.body:
                    method_compiler.compile_node(s)
                    if method_compiler._is_expression(s):
                        method_compiler.code.emit(OpCode.POP_TOP)

                none_idx = method_compiler.code.add_constant(None)
                method_compiler.code.emit(OpCode.LOAD_CONST, none_idx)
                method_compiler.code.emit(OpCode.RETURN_VALUE)

                for default in stmt.defaults:
                    self.compile_node(default)

                code_idx = self.code.add_constant(method_compiler.code)
                self.code.emit(OpCode.LOAD_CONST, code_idx, stmt.line)
                self.code.emit(OpCode.MAKE_FUNCTION, len(stmt.defaults), stmt.line)

                method_names.append(stmt.name)
            elif isinstance(stmt, AssignmentNode):
                self.compile_node(stmt.value)
                method_names.append(f"__classvar__{stmt.target}")

        class_name_idx = self.code.add_constant(node.name)
        self.code.emit(OpCode.LOAD_CONST, class_name_idx, node.line)

        names_idx = self.code.add_constant(method_names)
        self.code.emit(OpCode.LOAD_CONST, names_idx, node.line)

        self.code.emit(OpCode.MAKE_CLASS, len(method_names), node.line)

        # Apply decorators (in reverse order)
        for decorator_node in reversed(node.decorators):
            self.compile_node(decorator_node)
            self.code.emit(OpCode.ROT_TWO, line=node.line)
            self.code.emit(OpCode.CALL_FUNCTION, 1, node.line)

        name_idx = self.code.add_name(node.name)
        self.code.emit(OpCode.STORE_NAME_DEFINE, name_idx, node.line)

    # ---------------------------------------------------------------- #
    #  Helpers                                                          #
    # ---------------------------------------------------------------- #

    def _is_expression(self, node: ASTNode) -> bool:
        """Check if a node is a pure expression (leaves a value on the stack)."""
        return isinstance(node, (
            NumberNode, StringNode, BooleanNode, NoneNode, IdentifierNode,
            FStringNode, ListNode, DictNode, BinaryOpNode, UnaryOpNode,
            FunctionCallNode, AttributeNode, IndexNode,
            TupleNode, ListCompNode, LambdaNode, TernaryNode, SliceNode,
        ))


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #

def compile_kilat(source: str, filename: str = '<kilat>') -> CodeObject:
    """Parse and compile Kilat source to bytecode."""
    from kilat_parser import parse_kilat
    ast = parse_kilat(source)
    compiler = KilatBytecodeCompiler(name=filename)
    return compiler.compile_program(ast)
