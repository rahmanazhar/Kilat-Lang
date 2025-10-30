"""
Kilat-Lang Interpreter
Executes AST directly without Python dependency
"""

from typing import Any, Dict, List, Optional
from kilat_ast import *
import sys


class BreakException(Exception):
    """Exception for break statement"""
    pass


class ContinueException(Exception):
    """Exception for continue statement"""
    pass


class ReturnException(Exception):
    """Exception for return statement"""
    def __init__(self, value):
        self.value = value


class KilatRuntimeError(Exception):
    """Runtime error in Kilat"""
    pass


class Environment:
    """Environment for variable storage"""
    
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any):
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise KilatRuntimeError(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any):
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            # If variable doesn't exist, define it
            self.variables[name] = value
    
    def exists(self, name: str) -> bool:
        return name in self.variables or (self.parent and self.parent.exists(name))


class KilatFunction:
    """Represents a user-defined function"""
    
    def __init__(self, name: str, parameters: List[str], defaults: List[ASTNode], body: List[ASTNode], closure: Environment):
        self.name = name
        self.parameters = parameters
        self.defaults = defaults
        self.body = body
        self.closure = closure
    
    def call(self, interpreter: 'KilatInterpreter', arguments: List[Any]) -> Any:
        # Create new environment for function
        func_env = Environment(parent=self.closure)
        
        # Bind parameters
        required_params = len(self.parameters) - len(self.defaults)
        
        if len(arguments) < required_params:
            raise KilatRuntimeError(f"Function {self.name} requires at least {required_params} arguments, got {len(arguments)}")
        
        if len(arguments) > len(self.parameters):
            raise KilatRuntimeError(f"Function {self.name} takes at most {len(self.parameters)} arguments, got {len(arguments)}")
        
        # Bind provided arguments
        for i, arg in enumerate(arguments):
            func_env.define(self.parameters[i], arg)
        
        # Bind default values for missing arguments
        for i in range(len(arguments), len(self.parameters)):
            default_index = i - required_params
            default_value = interpreter.eval(self.defaults[default_index], func_env)
            func_env.define(self.parameters[i], default_value)
        
        # Execute function body
        try:
            for stmt in self.body:
                interpreter.execute(stmt, func_env)
            return None
        except ReturnException as e:
            return e.value


class KilatClass:
    """Represents a user-defined class"""
    
    def __init__(self, name: str, base_class: Optional['KilatClass'], methods: Dict[str, KilatFunction]):
        self.name = name
        self.base_class = base_class
        self.methods = methods
    
    def instantiate(self, interpreter: 'KilatInterpreter', arguments: List[Any]) -> 'KilatInstance':
        instance = KilatInstance(self)
        
        # Call __init__ if it exists
        if '__init__' in self.methods:
            init_method = self.methods['__init__']
            init_method.call(interpreter, [instance] + arguments)
        
        return instance


class KilatInstance:
    """Represents an instance of a class"""
    
    def __init__(self, klass: KilatClass):
        self.klass = klass
        self.attributes: Dict[str, Any] = {}
    
    def get(self, name: str, interpreter: 'KilatInterpreter') -> Any:
        # Check instance attributes
        if name in self.attributes:
            return self.attributes[name]
        
        # Check class methods
        if name in self.klass.methods:
            method = self.klass.methods[name]
            # Return a bound method
            return lambda *args: method.call(interpreter, [self] + list(args))
        
        # Check base class
        if self.klass.base_class:
            if name in self.klass.base_class.methods:
                method = self.klass.base_class.methods[name]
                return lambda *args: method.call(interpreter, [self] + list(args))
        
        raise KilatRuntimeError(f"Attribute '{name}' not found")
    
    def set(self, name: str, value: Any):
        self.attributes[name] = value


class KilatInterpreter:
    """Interpreter for Kilat-Lang AST"""
    
    def __init__(self):
        self.global_env = Environment()
        self.setup_builtins()
    
    def setup_builtins(self):
        """Setup built-in functions"""
        # cetak (print)
        def builtin_cetak(*args, **kwargs):
            end = kwargs.get('end', '\n')
            sep = kwargs.get('sep', ' ')
            print(*args, sep=sep, end=end)
        
        # input
        def builtin_input(prompt=''):
            return input(prompt)
        
        # panjang (len)
        def builtin_panjang(obj):
            return len(obj)
        
        # julat (range)
        def builtin_julat(*args):
            return list(range(*args))
        
        # jenis (type)
        def builtin_jenis(obj):
            return type(obj).__name__
        
        # Type conversions
        def builtin_int(x):
            return int(x)
        
        def builtin_float(x):
            return float(x)
        
        def builtin_str(x):
            return str(x)
        
        def builtin_list(x):
            return list(x)
        
        # Register builtins
        self.global_env.define('cetak', builtin_cetak)
        self.global_env.define('input', builtin_input)
        self.global_env.define('panjang', builtin_panjang)
        self.global_env.define('julat', builtin_julat)
        self.global_env.define('jenis', builtin_jenis)
        self.global_env.define('int', builtin_int)
        self.global_env.define('float', builtin_float)
        self.global_env.define('str', builtin_str)
        self.global_env.define('list', builtin_list)
    
    def interpret(self, program: ProgramNode):
        """Interpret the program"""
        try:
            for statement in program.statements:
                self.execute(statement, self.global_env)
        except KilatRuntimeError as e:
            print(f"Runtime Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def execute(self, node: ASTNode, env: Environment) -> Any:
        """Execute a statement"""
        if isinstance(node, AssignmentNode):
            value = self.eval(node.value, env)
            env.set(node.target, value)
            return None
        
        elif isinstance(node, IfNode):
            condition = self.eval(node.condition, env)
            if self.is_truthy(condition):
                for stmt in node.then_body:
                    self.execute(stmt, env)
            else:
                # Check elif parts
                executed = False
                for elif_cond, elif_body in node.elif_parts:
                    if self.is_truthy(self.eval(elif_cond, env)):
                        for stmt in elif_body:
                            self.execute(stmt, env)
                        executed = True
                        break
                
                # Execute else if no elif matched
                if not executed and node.else_body:
                    for stmt in node.else_body:
                        self.execute(stmt, env)
            return None
        
        elif isinstance(node, WhileNode):
            while self.is_truthy(self.eval(node.condition, env)):
                try:
                    for stmt in node.body:
                        self.execute(stmt, env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return None
        
        elif isinstance(node, ForNode):
            iterable = self.eval(node.iterable, env)
            for item in iterable:
                env.set(node.variable, item)
                try:
                    for stmt in node.body:
                        self.execute(stmt, env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return None
        
        elif isinstance(node, BreakNode):
            raise BreakException()
        
        elif isinstance(node, ContinueNode):
            raise ContinueException()
        
        elif isinstance(node, ReturnNode):
            value = None if node.value is None else self.eval(node.value, env)
            raise ReturnException(value)
        
        elif isinstance(node, FunctionDefNode):
            function = KilatFunction(node.name, node.parameters, node.defaults, node.body, env)
            env.define(node.name, function)
            return None
        
        elif isinstance(node, ClassDefNode):
            # Evaluate methods
            methods = {}
            for stmt in node.body:
                if isinstance(stmt, FunctionDefNode):
                    method = KilatFunction(stmt.name, stmt.parameters, stmt.defaults, stmt.body, env)
                    methods[stmt.name] = method
            
            # Get base class if any
            base_class = None
            if node.base_class:
                base_class = env.get(node.base_class)
                if not isinstance(base_class, KilatClass):
                    raise KilatRuntimeError(f"{node.base_class} is not a class")
            
            klass = KilatClass(node.name, base_class, methods)
            env.define(node.name, klass)
            return None
        
        elif isinstance(node, TryNode):
            try:
                for stmt in node.try_body:
                    self.execute(stmt, env)
            except Exception as e:
                # Handle except clauses
                handled = False
                for exception_type, except_body in node.except_clauses:
                    # For simplicity, catch all exceptions if no type specified
                    if exception_type is None or exception_type == type(e).__name__:
                        for stmt in except_body:
                            self.execute(stmt, env)
                        handled = True
                        break
                
                if not handled:
                    raise
            finally:
                if node.finally_body:
                    for stmt in node.finally_body:
                        self.execute(stmt, env)
            return None
        
        elif isinstance(node, RaiseNode):
            exception_obj = self.eval(node.exception, env)
            raise Exception(str(exception_obj))
        
        # Expression statements
        else:
            return self.eval(node, env)
    
    def eval(self, node: ASTNode, env: Environment) -> Any:
        """Evaluate an expression"""
        if isinstance(node, NumberNode):
            return node.value
        
        elif isinstance(node, StringNode):
            return node.value
        
        elif isinstance(node, BooleanNode):
            return node.value
        
        elif isinstance(node, NoneNode):
            return None
        
        elif isinstance(node, IdentifierNode):
            return env.get(node.name)
        
        elif isinstance(node, ListNode):
            return [self.eval(elem, env) for elem in node.elements]
        
        elif isinstance(node, DictNode):
            result = {}
            for key_node, value_node in node.pairs:
                key = self.eval(key_node, env)
                value = self.eval(value_node, env)
                result[key] = value
            return result
        
        elif isinstance(node, BinaryOpNode):
            left = self.eval(node.left, env)
            right = self.eval(node.right, env)
            
            if node.operator == '+':
                return left + right
            elif node.operator == '-':
                return left - right
            elif node.operator == '*':
                return left * right
            elif node.operator == '/':
                return left / right
            elif node.operator == '//':
                return left // right
            elif node.operator == '%':
                return left % right
            elif node.operator == '**':
                return left ** right
            elif node.operator == '==':
                return left == right
            elif node.operator == '!=':
                return left != right
            elif node.operator == '<':
                return left < right
            elif node.operator == '>':
                return left > right
            elif node.operator == '<=':
                return left <= right
            elif node.operator == '>=':
                return left >= right
            elif node.operator == 'dan':
                return left and right
            elif node.operator == 'atau_logik':
                return left or right
            elif node.operator == 'dalam':
                return left in right
            elif node.operator == 'adalah':
                return left is right
            else:
                raise KilatRuntimeError(f"Unknown operator: {node.operator}")
        
        elif isinstance(node, UnaryOpNode):
            operand = self.eval(node.operand, env)
            
            if node.operator == '-':
                return -operand
            elif node.operator == 'bukan':
                return not operand
            else:
                raise KilatRuntimeError(f"Unknown unary operator: {node.operator}")
        
        elif isinstance(node, FunctionCallNode):
            # Get function
            if isinstance(node.function, str):
                func = env.get(node.function)
            else:
                func = self.eval(node.function, env)
            
            # Evaluate arguments
            arguments = [self.eval(arg, env) for arg in node.arguments]
            
            # Call function
            if isinstance(func, KilatFunction):
                return func.call(self, arguments)
            elif isinstance(func, KilatClass):
                return func.instantiate(self, arguments)
            elif callable(func):
                # Built-in function
                return func(*arguments)
            else:
                raise KilatRuntimeError(f"{node.function} is not callable")
        
        elif isinstance(node, AttributeNode):
            obj = self.eval(node.object, env)
            
            if isinstance(obj, KilatInstance):
                return obj.get(node.attribute, self)
            else:
                # Try to get Python attribute
                try:
                    return getattr(obj, node.attribute)
                except AttributeError:
                    raise KilatRuntimeError(f"Attribute '{node.attribute}' not found")
        
        elif isinstance(node, IndexNode):
            obj = self.eval(node.object, env)
            index = self.eval(node.index, env)
            return obj[index]
        
        else:
            raise KilatRuntimeError(f"Cannot evaluate node type: {type(node).__name__}")
    
    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy"""
        if value is None or value is False:
            return False
        if value == 0 or value == '' or value == []:
            return False
        return True


def run_kilat(source: str):
    """Parse and execute Kilat source code"""
    from kilat_parser import parse_kilat
    
    ast = parse_kilat(source)
    interpreter = KilatInterpreter()
    interpreter.interpret(ast)
