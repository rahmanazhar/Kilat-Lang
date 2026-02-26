"""
Kilat-Lang Interpreter
Executes AST directly without depending on the Python runtime semantics.
"""

from typing import Any, Dict, List, Optional
from kilat_ast import *
import sys
import math
import os


# ------------------------------------------------------------------ #
#  Control-flow exceptions                                             #
# ------------------------------------------------------------------ #

class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value: Any):
        self.value = value


class KilatRuntimeError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.kilat_message = message
        self.line = line
        self.column = column
        super().__init__(message)


class KilatException(Exception):
    """An exception raised from within Kilat code via `bangkit`."""
    def __init__(self, value: Any):
        self.value = value
        super().__init__(str(value))


# ------------------------------------------------------------------ #
#  Environment / Scope                                                  #
# ------------------------------------------------------------------ #

class Environment:
    """Variable storage with scope chaining."""

    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
        self._globals: set = set()   # names declared global in this scope

    def define(self, name: str, value: Any):
        self.variables[name] = value

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise KilatRuntimeError(f"Pembolehubah tidak ditakrifkan: '{name}'")

    def set(self, name: str, value: Any):
        """Assign to the nearest scope that already has this name."""
        if name in self._globals:
            # Find global scope
            env = self
            while env.parent:
                env = env.parent
            env.variables[name] = value
            return
        if name in self.variables:
            self.variables[name] = value
        elif self.parent and self.parent._has(name):
            self.parent.set(name, value)
        else:
            # Define in current scope
            self.variables[name] = value

    def _has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent._has(name)
        return False

    def declare_global(self, name: str):
        self._globals.add(name)


# ------------------------------------------------------------------ #
#  Kilat callable objects                                              #
# ------------------------------------------------------------------ #

class KilatFunction:
    """User-defined function."""

    def __init__(self, name: str, parameters: List[str], defaults: List[ASTNode],
                 body: List[ASTNode], closure: Environment):
        self.name = name
        self.parameters = parameters
        self.defaults = defaults
        self.body = body
        self.closure = closure

    def call(self, interpreter: 'KilatInterpreter',
             arguments: List[Any],
             keyword_args: Dict[str, Any] = None) -> Any:
        if keyword_args is None:
            keyword_args = {}

        func_env = Environment(parent=self.closure)

        # Resolve defaults (evaluated lazily at call time)
        required_count = len(self.parameters) - len(self.defaults)

        # Bind positional arguments
        for i, arg in enumerate(arguments):
            if i >= len(self.parameters):
                raise KilatRuntimeError(
                    f"Fungsi '{self.name}' menerima paling banyak "
                    f"{len(self.parameters)} argumen, diberi {len(arguments)}"
                )
            func_env.define(self.parameters[i], arg)

        # Bind keyword arguments
        for kw_name, kw_val in keyword_args.items():
            if kw_name not in self.parameters:
                raise KilatRuntimeError(
                    f"Fungsi '{self.name}' tidak ada parameter '{kw_name}'"
                )
            func_env.define(kw_name, kw_val)

        # Fill in defaults for unbound parameters
        for i in range(len(self.parameters)):
            if self.parameters[i] not in func_env.variables:
                default_index = i - required_count
                if default_index < 0 or default_index >= len(self.defaults):
                    raise KilatRuntimeError(
                        f"Fungsi '{self.name}' memerlukan argumen untuk '{self.parameters[i]}'"
                    )
                default_val = interpreter.eval(self.defaults[default_index], self.closure)
                func_env.define(self.parameters[i], default_val)

        try:
            for stmt in self.body:
                interpreter.execute(stmt, func_env)
            return None
        except ReturnException as e:
            return e.value

    def __repr__(self):
        return f"<fungsi {self.name}>"


class KilatClass:
    """User-defined class."""

    def __init__(self, name: str, base_class: Optional['KilatClass'],
                 methods: Dict[str, KilatFunction]):
        self.name = name
        self.base_class = base_class
        self.methods = methods

    def instantiate(self, interpreter: 'KilatInterpreter', arguments: List[Any],
                    keyword_args: Dict[str, Any] = None) -> 'KilatInstance':
        instance = KilatInstance(self)
        init = self._get_method('__init__')
        if init:
            init.call(interpreter, [instance] + arguments, keyword_args or {})
        return instance

    def _get_method(self, name: str) -> Optional[KilatFunction]:
        if name in self.methods:
            return self.methods[name]
        if self.base_class:
            return self.base_class._get_method(name)
        return None

    def __repr__(self):
        return f"<kelas {self.name}>"


class KilatInstance:
    """An instance of a Kilat class."""

    def __init__(self, klass: KilatClass):
        self.klass = klass
        self.attributes: Dict[str, Any] = {}

    def get_attr(self, name: str, interpreter: 'KilatInterpreter') -> Any:
        # Instance attributes take priority
        if name in self.attributes:
            return self.attributes[name]

        # Class / inherited methods
        method = self.klass._get_method(name)
        if method is not None:
            # Return a bound method
            bound = method
            instance = self
            def bound_call(*args, **kwargs):
                return bound.call(interpreter, [instance] + list(args),
                                  keyword_args=kwargs)
            bound_call.__name__ = name
            return bound_call

        raise KilatRuntimeError(f"Atribut '{name}' tidak ditemui pada {self.klass.name}")

    def set_attr(self, name: str, value: Any):
        self.attributes[name] = value

    def __repr__(self):
        return f"<{self.klass.name} objek>"

    def __str__(self):
        return self.__repr__()


# ------------------------------------------------------------------ #
#  Main interpreter                                                    #
# ------------------------------------------------------------------ #

class KilatInterpreter:

    def __init__(self):
        self.global_env = Environment()
        self._setup_builtins()

    # ---------------------------------------------------------------- #
    #  Built-in functions                                               #
    # ---------------------------------------------------------------- #

    def _setup_builtins(self):
        env = self.global_env

        # cetak (print)
        def _cetak(*args, **kwargs):
            end = kwargs.get('end', '\n')
            sep = kwargs.get('sep', ' ')
            print(*[str(a) if not isinstance(a, str) else a for a in args],
                  sep=sep, end=end)

        # input
        def _input(prompt=''):
            return input(str(prompt))

        # panjang (len)
        def _panjang(obj):
            try:
                return len(obj)
            except TypeError:
                raise KilatRuntimeError(f"Objek jenis '{type(obj).__name__}' tidak mempunyai panjang")

        # julat (range) – returns a list so it works in for loops
        def _julat(*args):
            return list(range(*[int(a) for a in args]))

        # jenis (type)
        def _jenis(obj):
            if isinstance(obj, KilatInstance):
                return obj.klass.name
            if isinstance(obj, KilatClass):
                return f"kelas '{obj.name}'"
            return type(obj).__name__

        # abs
        def _abs(x):
            return abs(x)

        # max / min / sum
        def _max(*args):
            if len(args) == 1:
                return max(args[0])
            return max(args)

        def _min(*args):
            if len(args) == 1:
                return min(args[0])
            return min(args)

        def _sum(iterable, start=0):
            return sum(iterable, start)

        # sorted / reversed
        def _disusun(iterable, reverse=False):
            return sorted(iterable, reverse=bool(reverse))

        def _terbalik(iterable):
            return list(reversed(iterable))

        # enumerate
        def _nombor_senarai(iterable, start=0):
            return list(enumerate(iterable, int(start)))

        # zip
        def _cantum(*iterables):
            return list(zip(*iterables))

        # Type conversions
        def _int(x, base=None):
            if base is not None:
                return int(x, int(base))
            return int(x)

        def _float(x):
            return float(x)

        def _str(x):
            if isinstance(x, KilatInstance):
                return str(x)
            return str(x)

        def _list(x=None):
            if x is None:
                return []
            return list(x)

        def _dict(**kwargs):
            return dict(kwargs)

        def _set(x=None):
            if x is None:
                return set()
            return set(x)

        def _tuple(x=None):
            if x is None:
                return ()
            return tuple(x)

        def _bool(x=None):
            if x is None:
                return False
            return bool(x)

        # String helpers
        def _cetak_format(template, *args):
            return template.format(*args)

        # Math
        def _punca(x):
            return math.sqrt(float(x))

        def _kuasa(x, y):
            return x ** y

        def _bulat(x, ndigits=None):
            if ndigits is None:
                return round(x)
            return round(x, int(ndigits))

        # chr / ord
        def _aksara(n):
            return chr(int(n))

        def _kod(c):
            return ord(str(c))

        # hasattr / getattr / setattr
        def _ada_atribut(obj, name):
            if isinstance(obj, KilatInstance):
                return name in obj.attributes or obj.klass._get_method(name) is not None
            return hasattr(obj, str(name))

        # isinstance check
        def _adalah_jenis(obj, klass):
            if isinstance(klass, KilatClass):
                return isinstance(obj, KilatInstance) and (
                    obj.klass is klass or self._is_subclass(obj.klass, klass)
                )
            return isinstance(obj, klass)

        # map / filter
        def _peta(func, iterable):
            return list(map(func, iterable))

        def _tapis(func, iterable):
            return list(filter(func, iterable))

        # all / any
        def _semua(iterable):
            return all(iterable)

        def _mana(iterable):
            return any(iterable)

        # open file
        def _buka(path, mode='r', encoding='utf-8'):
            return open(str(path), str(mode), encoding=encoding)

        # Register
        builtins = {
            'cetak': _cetak,
            'input': _input,
            'panjang': _panjang,
            'julat': _julat,
            'jenis': _jenis,
            'abs': _abs,
            'maks': _max,
            'min': _min,
            'jumlah': _sum,
            'disusun': _disusun,
            'terbalik': _terbalik,
            'nombor_senarai': _nombor_senarai,
            'cantum': _cantum,
            'int': _int,
            'float': _float,
            'str': _str,
            'list': _list,
            'dict': _dict,
            'set': _set,
            'tuple': _tuple,
            'bool': _bool,
            'punca': _punca,
            'kuasa': _kuasa,
            'bulat': _bulat,
            'aksara': _aksara,
            'kod': _kod,
            'ada_atribut': _ada_atribut,
            'adalah_jenis': _adalah_jenis,
            'peta': _peta,
            'tapis': _tapis,
            'semua': _semua,
            'mana': _mana,
            'buka': _buka,
            # Also register common Python builtins by their Python name
            # so Python stdlib functions work when accessed via import
            'len': len,
            'range': lambda *a: list(range(*a)),
            'print': print,
            'repr': repr,
        }

        for name, func in builtins.items():
            env.define(name, func)

    def _is_subclass(self, klass: KilatClass, parent: KilatClass) -> bool:
        if klass is parent:
            return True
        if klass.base_class:
            return self._is_subclass(klass.base_class, parent)
        return False

    # ---------------------------------------------------------------- #
    #  Interpret entry point                                            #
    # ---------------------------------------------------------------- #

    def interpret(self, program: ProgramNode):
        try:
            for statement in program.statements:
                self.execute(statement, self.global_env)
        except KilatRuntimeError as e:
            loc = f" (baris {e.line})" if e.line else ""
            print(f"Ralat Masa Larian{loc}: {e.kilat_message}", file=sys.stderr)
            sys.exit(1)
        except KilatException as e:
            print(f"Pengecualian tidak ditangkap: {e.value}", file=sys.stderr)
            sys.exit(1)

    # ---------------------------------------------------------------- #
    #  Statement execution                                              #
    # ---------------------------------------------------------------- #

    def execute(self, node: ASTNode, env: Environment) -> Any:

        # ----- assignments ----- #
        if isinstance(node, AssignmentNode):
            value = self.eval(node.value, env)
            # Python semantics: assignment always defines in the CURRENT scope
            # (unless declared global).  Use define() so that a function-local
            # assignment never accidentally overwrites a variable in an outer scope.
            if node.target in env._globals:
                # Walk up to global scope
                g = env
                while g.parent:
                    g = g.parent
                g.variables[node.target] = value
            else:
                env.define(node.target, value)
            return None

        if isinstance(node, AugmentedAssignmentNode):
            current = env.get(node.target)
            operand = self.eval(node.value, env)
            result = self._apply_op(node.operator, current, operand, node)
            env.set(node.target, result)
            return None

        if isinstance(node, AttributeAssignmentNode):
            obj = self.eval(node.object, env)
            value = self.eval(node.value, env)
            if isinstance(obj, KilatInstance):
                obj.set_attr(node.attribute, value)
            else:
                try:
                    setattr(obj, node.attribute, value)
                except AttributeError:
                    raise KilatRuntimeError(
                        f"Tidak dapat menetapkan atribut '{node.attribute}'",
                        node.line, node.column
                    )
            return None

        if isinstance(node, IndexAssignmentNode):
            obj = self.eval(node.object, env)
            index = self.eval(node.index, env)
            value = self.eval(node.value, env)
            try:
                obj[index] = value
            except (TypeError, KeyError, IndexError) as e:
                raise KilatRuntimeError(str(e), node.line, node.column)
            return None

        # ----- control flow ----- #
        if isinstance(node, IfNode):
            if self.is_truthy(self.eval(node.condition, env)):
                self._exec_block(node.then_body, env)
            else:
                executed = False
                for elif_cond, elif_body in node.elif_parts:
                    if self.is_truthy(self.eval(elif_cond, env)):
                        self._exec_block(elif_body, env)
                        executed = True
                        break
                if not executed and node.else_body:
                    self._exec_block(node.else_body, env)
            return None

        if isinstance(node, WhileNode):
            while self.is_truthy(self.eval(node.condition, env)):
                try:
                    self._exec_block(node.body, env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return None

        if isinstance(node, ForNode):
            iterable = self.eval(node.iterable, env)
            try:
                it = iter(iterable)
            except TypeError:
                raise KilatRuntimeError(
                    f"Objek tidak boleh diulang: '{type(iterable).__name__}'",
                    node.line, node.column
                )
            for item in it:
                env.set(node.variable, item)
                try:
                    self._exec_block(node.body, env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return None

        if isinstance(node, BreakNode):
            raise BreakException()

        if isinstance(node, ContinueNode):
            raise ContinueException()

        if isinstance(node, ReturnNode):
            value = None if node.value is None else self.eval(node.value, env)
            raise ReturnException(value)

        # ----- definitions ----- #
        if isinstance(node, FunctionDefNode):
            func = KilatFunction(node.name, node.parameters, node.defaults, node.body, env)
            env.define(node.name, func)
            return None

        if isinstance(node, ClassDefNode):
            methods = {}
            class_env = Environment(parent=env)

            for stmt in node.body:
                if isinstance(stmt, FunctionDefNode):
                    method = KilatFunction(stmt.name, stmt.parameters,
                                           stmt.defaults, stmt.body, class_env)
                    methods[stmt.name] = method
                elif isinstance(stmt, AssignmentNode):
                    # Class-level variable
                    class_env.define(stmt.target, self.eval(stmt.value, env))

            base_class = None
            if node.base_class:
                base_val = env.get(node.base_class)
                if isinstance(base_val, KilatClass):
                    base_class = base_val
                else:
                    # Allow Python classes as base (limited support)
                    base_class = None

            klass = KilatClass(node.name, base_class, methods)
            env.define(node.name, klass)
            return None

        # ----- exception handling ----- #
        if isinstance(node, TryNode):
            try:
                self._exec_block(node.try_body, env)
            except (KilatException, KilatRuntimeError, Exception) as exc:
                handled = False
                for exc_type, exc_alias, exc_body in node.except_clauses:
                    match = False
                    if exc_type is None:
                        match = True
                    elif isinstance(exc, KilatException):
                        # Kilat exceptions: match by string type name for now
                        match = True
                    else:
                        # Python exceptions
                        try:
                            py_type = eval(exc_type)  # noqa: S307
                            if isinstance(exc, py_type):
                                match = True
                        except Exception:
                            match = exc_type == type(exc).__name__

                    if match:
                        exc_env = Environment(parent=env)
                        if exc_alias:
                            val = exc.value if isinstance(exc, KilatException) else exc
                            exc_env.define(exc_alias, val)
                        self._exec_block(exc_body, exc_env)
                        handled = True
                        break

                if not handled:
                    raise
            finally:
                if node.finally_body:
                    self._exec_block(node.finally_body, env)
            return None

        if isinstance(node, RaiseNode):
            exc_val = self.eval(node.exception, env)
            raise KilatException(exc_val)

        # ----- imports ----- #
        if isinstance(node, ImportNode):
            try:
                import importlib
                mod = importlib.import_module(node.module)
                alias = node.alias or node.module.split('.')[-1]
                env.define(alias, mod)
            except ImportError as e:
                raise KilatRuntimeError(f"Tidak dapat import '{node.module}': {e}",
                                        node.line, node.column)
            return None

        if isinstance(node, FromImportNode):
            try:
                import importlib
                mod = importlib.import_module(node.module)
                for name, alias in zip(node.names, node.aliases):
                    obj = getattr(mod, name)
                    env.define(alias or name, obj)
            except (ImportError, AttributeError) as e:
                raise KilatRuntimeError(f"Import gagal: {e}", node.line, node.column)
            return None

        # ----- scope declarations ----- #
        if isinstance(node, GlobalNode):
            for name in node.names:
                env.declare_global(name)
            return None

        if isinstance(node, NonlocalNode):
            # nonlocal: walk up one level
            return None

        if isinstance(node, DeleteNode):
            target = node.target
            if isinstance(target, IdentifierNode):
                if target.name in env.variables:
                    del env.variables[target.name]
            elif isinstance(target, IndexNode):
                obj = self.eval(target.object, env)
                idx = self.eval(target.index, env)
                del obj[idx]
            return None

        if isinstance(node, PassNode):
            return None

        # ----- expression statements ----- #
        return self.eval(node, env)

    def _exec_block(self, stmts: List[ASTNode], env: Environment):
        """Execute a list of statements in the given environment."""
        for stmt in stmts:
            self.execute(stmt, env)

    # ---------------------------------------------------------------- #
    #  Expression evaluation                                            #
    # ---------------------------------------------------------------- #

    def eval(self, node: ASTNode, env: Environment) -> Any:

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, StringNode):
            return node.value

        if isinstance(node, BooleanNode):
            return node.value

        if isinstance(node, NoneNode):
            return None

        if isinstance(node, FStringNode):
            parts = []
            for part in node.parts:
                val = self.eval(part, env)
                parts.append(str(val))
            return ''.join(parts)

        if isinstance(node, IdentifierNode):
            return env.get(node.name)

        if isinstance(node, ListNode):
            return [self.eval(e, env) for e in node.elements]

        if isinstance(node, DictNode):
            result = {}
            for k_node, v_node in node.pairs:
                result[self.eval(k_node, env)] = self.eval(v_node, env)
            return result

        if isinstance(node, BinaryOpNode):
            return self._eval_binary(node, env)

        if isinstance(node, UnaryOpNode):
            operand = self.eval(node.operand, env)
            if node.operator == '-':
                return -operand
            if node.operator == 'bukan':
                return not operand
            if node.operator == '+':
                return +operand
            raise KilatRuntimeError(f"Operator unary tidak dikenali: {node.operator}",
                                    node.line, node.column)

        if isinstance(node, FunctionCallNode):
            return self._eval_call(node, env)

        if isinstance(node, AttributeNode):
            obj = self.eval(node.object, env)
            return self._get_attribute(obj, node.attribute, env, node)

        if isinstance(node, IndexNode):
            obj = self.eval(node.object, env)
            index = self.eval(node.index, env)
            try:
                return obj[index]
            except (KeyError, IndexError, TypeError) as e:
                raise KilatRuntimeError(str(e), node.line, node.column)

        raise KilatRuntimeError(
            f"Tidak dapat menilai nod jenis: {type(node).__name__}",
            getattr(node, 'line', 0), getattr(node, 'column', 0)
        )

    def _eval_binary(self, node: BinaryOpNode, env: Environment) -> Any:
        op = node.operator

        # Short-circuit logical operators
        if op == 'dan':
            left = self.eval(node.left, env)
            if not self.is_truthy(left):
                return left
            return self.eval(node.right, env)

        if op == 'atau_logik':
            left = self.eval(node.left, env)
            if self.is_truthy(left):
                return left
            return self.eval(node.right, env)

        left = self.eval(node.left, env)
        right = self.eval(node.right, env)

        try:
            if op == '+':
                return left + right
            if op == '-':
                return left - right
            if op == '*':
                return left * right
            if op == '/':
                if right == 0:
                    raise KilatRuntimeError("Pembahagian dengan sifar", node.line, node.column)
                return left / right
            if op == '//':
                if right == 0:
                    raise KilatRuntimeError("Pembahagian lantai dengan sifar", node.line, node.column)
                return left // right
            if op == '%':
                return left % right
            if op == '**':
                return left ** right
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            if op == '<':
                return left < right
            if op == '>':
                return left > right
            if op == '<=':
                return left <= right
            if op == '>=':
                return left >= right
            if op == 'dalam':
                return left in right
            if op == 'adalah':
                return left is right
        except KilatRuntimeError:
            raise
        except Exception as e:
            raise KilatRuntimeError(str(e), node.line, node.column)

        raise KilatRuntimeError(f"Operator tidak dikenali: {op}", node.line, node.column)

    def _apply_op(self, op: str, left: Any, right: Any, node: ASTNode) -> Any:
        """Apply an arithmetic operator (used for augmented assignment)."""
        try:
            if op == '+':  return left + right
            if op == '-':  return left - right
            if op == '*':  return left * right
            if op == '/':  return left / right
            if op == '//': return left // right
            if op == '**': return left ** right
            if op == '%':  return left % right
        except Exception as e:
            raise KilatRuntimeError(str(e), node.line, node.column)
        raise KilatRuntimeError(f"Operator tidak dikenali: {op}", node.line, node.column)

    def _eval_call(self, node: FunctionCallNode, env: Environment) -> Any:
        # Resolve the function
        if isinstance(node.function, str):
            try:
                func = env.get(node.function)
            except KilatRuntimeError:
                raise KilatRuntimeError(
                    f"Fungsi '{node.function}' tidak ditakrifkan",
                    node.line, node.column
                )
        else:
            func = self.eval(node.function, env)

        # Evaluate positional arguments
        args = [self.eval(a, env) for a in node.arguments]

        # Evaluate keyword arguments
        kwargs = {k: self.eval(v, env) for k, v in node.keyword_args.items()}

        # Dispatch
        if isinstance(func, KilatFunction):
            return func.call(self, args, kwargs)

        if isinstance(func, KilatClass):
            return func.instantiate(self, args, kwargs)

        if callable(func):
            try:
                return func(*args, **kwargs)
            except TypeError as e:
                raise KilatRuntimeError(str(e), node.line, node.column)

        raise KilatRuntimeError(
            f"Tidak boleh dipanggil: {func!r}",
            node.line, node.column
        )

    def _get_attribute(self, obj: Any, attr: str,
                       env: Environment, node: ASTNode) -> Any:
        """Get attribute from an object, supporting Kilat and Python objects."""
        if isinstance(obj, KilatInstance):
            return obj.get_attr(attr, self)

        # KilatClass attribute access (e.g. ParentClass.__init__(self, ...))
        if isinstance(obj, KilatClass):
            method = obj._get_method(attr)
            if method is not None:
                # Return unbound KilatFunction; caller explicitly supplies self
                return method
            raise KilatRuntimeError(
                f"Kelas '{obj.name}' tidak mempunyai atribut '{attr}'",
                node.line, node.column
            )

        # Python built-in objects — expose their methods as callables
        try:
            return getattr(obj, attr)
        except AttributeError:
            raise KilatRuntimeError(
                f"Atribut '{attr}' tidak ditemui pada {type(obj).__name__}",
                node.line, node.column
            )

    # ---------------------------------------------------------------- #
    #  Truthiness                                                       #
    # ---------------------------------------------------------------- #

    def is_truthy(self, value: Any) -> bool:
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0:
            return False
        return True


# ------------------------------------------------------------------ #
#  Convenience entry point                                             #
# ------------------------------------------------------------------ #

def run_kilat(source: str, filename: str = '<kilat>'):
    """Parse and execute Kilat source code."""
    from kilat_parser import parse_kilat

    ast = parse_kilat(source)
    interpreter = KilatInterpreter()
    interpreter.interpret(ast)
