"""
Kilat-Lang Virtual Machine
Stack-based bytecode execution engine.
"""

from typing import Any, Dict, List, Optional
from kilat_bytecode import OpCode, CodeObject, Instruction
from kilat_interpreter import (
    Environment, KilatRuntimeError, KilatException,
    KilatClass, KilatInstance,
)
import sys
import math


# ------------------------------------------------------------------ #
#  Control-flow signals                                                #
# ------------------------------------------------------------------ #

class VMBreak(Exception):
    pass


class VMContinue(Exception):
    def __init__(self, target: int):
        self.target = target


class VMReturn(Exception):
    def __init__(self, value: Any):
        self.value = value


# ------------------------------------------------------------------ #
#  Bytecode function (wraps CodeObject)                                #
# ------------------------------------------------------------------ #

class VMFunction:
    """A compiled function (stores CodeObject instead of AST body)."""

    def __init__(self, name: str, code: CodeObject, defaults: list,
                 closure: Environment):
        self.name = name
        self.code = code
        self.defaults = defaults
        self.closure = closure

    def __repr__(self):
        return f"<fungsi {self.name}>"


# ------------------------------------------------------------------ #
#  Frame                                                               #
# ------------------------------------------------------------------ #

class Frame:
    """A single execution frame (one per function call / module)."""

    __slots__ = ('code', 'stack', 'env', 'ip', 'try_stack', 'current_exception')

    def __init__(self, code: CodeObject, env: Environment):
        self.code = code
        self.stack: list = []
        self.env = env
        self.ip: int = 0
        self.try_stack: list = []  # stack of (handler_addr, finally_addr)
        self.current_exception = None

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]


# ------------------------------------------------------------------ #
#  Virtual Machine                                                     #
# ------------------------------------------------------------------ #

class KilatVM:
    """Stack-based virtual machine for Kilat bytecode."""

    def __init__(self):
        self.global_env = Environment()
        self._setup_builtins()

    # ---------------------------------------------------------------- #
    #  Built-in functions (same as interpreter)                         #
    # ---------------------------------------------------------------- #

    def _setup_builtins(self):
        env = self.global_env

        def _cetak(*args, **kwargs):
            end = kwargs.get('end', '\n')
            sep = kwargs.get('sep', ' ')
            print(*[str(a) if not isinstance(a, str) else a for a in args],
                  sep=sep, end=end)

        def _input(prompt=''):
            return input(str(prompt))

        def _panjang(obj):
            try:
                return len(obj)
            except TypeError:
                raise KilatRuntimeError(f"Objek jenis '{type(obj).__name__}' tidak mempunyai panjang")

        def _julat(*args):
            return list(range(*[int(a) for a in args]))

        def _jenis(obj):
            if isinstance(obj, KilatInstance):
                return obj.klass.name
            if isinstance(obj, KilatClass):
                return f"kelas '{obj.name}'"
            return type(obj).__name__

        def _abs(x):
            return abs(x)

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

        def _disusun(iterable, reverse=False):
            return sorted(iterable, reverse=bool(reverse))

        def _terbalik(iterable):
            return list(reversed(iterable))

        def _nombor_senarai(iterable, start=0):
            return list(enumerate(iterable, int(start)))

        def _cantum(*iterables):
            return list(zip(*iterables))

        def _int(x, base=None):
            if base is not None:
                return int(x, int(base))
            return int(x)

        def _float(x):
            return float(x)

        def _str(x):
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

        def _punca(x):
            return math.sqrt(float(x))

        def _kuasa(x, y):
            return x ** y

        def _bulat(x, ndigits=None):
            if ndigits is None:
                return round(x)
            return round(x, int(ndigits))

        def _aksara(n):
            return chr(int(n))

        def _kod(c):
            return ord(str(c))

        def _ada_atribut(obj, name):
            if isinstance(obj, KilatInstance):
                return name in obj.attributes or obj.klass._get_method(name) is not None
            return hasattr(obj, str(name))

        def _adalah_jenis(obj, klass):
            if isinstance(klass, KilatClass):
                return isinstance(obj, KilatInstance) and (
                    obj.klass is klass or self._is_subclass(obj.klass, klass)
                )
            return isinstance(obj, klass)

        def _peta(func, iterable):
            return list(map(func, iterable))

        def _tapis(func, iterable):
            return list(filter(func, iterable))

        def _semua(iterable):
            return all(iterable)

        def _mana(iterable):
            return any(iterable)

        def _buka(path, mode='r', encoding='utf-8'):
            return open(str(path), str(mode), encoding=encoding)

        builtins = {
            'cetak': _cetak, 'input': _input, 'panjang': _panjang,
            'julat': _julat, 'jenis': _jenis, 'abs': _abs,
            'maks': _max, 'min': _min, 'jumlah': _sum,
            'disusun': _disusun, 'terbalik': _terbalik,
            'nombor_senarai': _nombor_senarai, 'cantum': _cantum,
            'int': _int, 'float': _float, 'str': _str,
            'list': _list, 'dict': _dict, 'set': _set,
            'tuple': _tuple, 'bool': _bool,
            'punca': _punca, 'kuasa': _kuasa, 'bulat': _bulat,
            'aksara': _aksara, 'kod': _kod,
            'ada_atribut': _ada_atribut, 'adalah_jenis': _adalah_jenis,
            'peta': _peta, 'tapis': _tapis,
            'semua': _semua, 'mana': _mana, 'buka': _buka,
            'len': len, 'range': lambda *a: list(range(*a)),
            'print': print, 'repr': repr,
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
    #  Run                                                              #
    # ---------------------------------------------------------------- #

    def run(self, code: CodeObject):
        """Execute a top-level CodeObject."""
        frame = Frame(code, self.global_env)
        try:
            self._execute_frame(frame)
        except KilatRuntimeError as e:
            loc = f" (baris {e.line})" if e.line else ""
            print(f"Ralat Masa Larian{loc}: {e.kilat_message}", file=sys.stderr)
            sys.exit(1)
        except KilatException as e:
            print(f"Pengecualian tidak ditangkap: {e.value}", file=sys.stderr)
            sys.exit(1)

    # ---------------------------------------------------------------- #
    #  Frame execution (main dispatch loop)                             #
    # ---------------------------------------------------------------- #

    def _execute_frame(self, frame: Frame) -> Any:
        code = frame.code
        instructions = code.instructions

        while frame.ip < len(instructions):
            instr = instructions[frame.ip]
            op = instr.opcode
            arg = instr.arg
            frame.ip += 1

            try:
                # ---- Stack manipulation ----
                if op == OpCode.NOP:
                    pass

                elif op == OpCode.POP_TOP:
                    if frame.stack:
                        frame.pop()

                elif op == OpCode.DUP_TOP:
                    frame.push(frame.peek())

                elif op == OpCode.ROT_TWO:
                    a = frame.pop()
                    b = frame.pop()
                    frame.push(a)
                    frame.push(b)

                # ---- Constants ----
                elif op == OpCode.LOAD_CONST:
                    frame.push(code.constants[arg])

                # ---- Names ----
                elif op == OpCode.LOAD_NAME:
                    name = code.names[arg]
                    frame.push(frame.env.get(name))

                elif op == OpCode.STORE_NAME:
                    name = code.names[arg]
                    frame.env.set(name, frame.pop())

                elif op == OpCode.STORE_NAME_DEFINE:
                    name = code.names[arg]
                    value = frame.pop()
                    if name in frame.env._globals:
                        g = frame.env
                        while g.parent:
                            g = g.parent
                        g.variables[name] = value
                    else:
                        frame.env.define(name, value)

                elif op == OpCode.LOAD_GLOBAL:
                    name = code.names[arg]
                    g = frame.env
                    while g.parent:
                        g = g.parent
                    if name in g.variables:
                        frame.push(g.variables[name])
                    else:
                        frame.push(frame.env.get(name))

                elif op == OpCode.STORE_GLOBAL:
                    name = code.names[arg]
                    value = frame.pop()
                    g = frame.env
                    while g.parent:
                        g = g.parent
                    g.variables[name] = value

                elif op == OpCode.DELETE_NAME:
                    name = code.names[arg]
                    if name in frame.env.variables:
                        del frame.env.variables[name]

                # ---- Attributes ----
                elif op == OpCode.LOAD_ATTR:
                    obj = frame.pop()
                    attr = code.names[arg]
                    frame.push(self._get_attribute(obj, attr, frame))

                elif op == OpCode.STORE_ATTR:
                    attr = code.names[arg]
                    value = frame.pop()
                    obj = frame.pop()
                    if isinstance(obj, KilatInstance):
                        obj.set_attr(attr, value)
                    else:
                        setattr(obj, attr, value)

                # ---- Indexing ----
                elif op == OpCode.LOAD_INDEX:
                    index = frame.pop()
                    obj = frame.pop()
                    try:
                        frame.push(obj[index])
                    except (KeyError, IndexError, TypeError) as e:
                        raise KilatRuntimeError(str(e), instr.line)

                elif op == OpCode.STORE_INDEX:
                    value = frame.pop()
                    index = frame.pop()
                    obj = frame.pop()
                    try:
                        obj[index] = value
                    except (TypeError, KeyError, IndexError) as e:
                        raise KilatRuntimeError(str(e), instr.line)

                elif op == OpCode.DELETE_INDEX:
                    index = frame.pop()
                    obj = frame.pop()
                    del obj[index]

                # ---- Arithmetic ----
                elif op == OpCode.BINARY_ADD:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left + right)

                elif op == OpCode.BINARY_SUB:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left - right)

                elif op == OpCode.BINARY_MUL:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left * right)

                elif op == OpCode.BINARY_DIV:
                    right = frame.pop()
                    left = frame.pop()
                    if right == 0:
                        raise KilatRuntimeError("Pembahagian dengan sifar", instr.line)
                    frame.push(left / right)

                elif op == OpCode.BINARY_FLOOR_DIV:
                    right = frame.pop()
                    left = frame.pop()
                    if right == 0:
                        raise KilatRuntimeError("Pembahagian lantai dengan sifar", instr.line)
                    frame.push(left // right)

                elif op == OpCode.BINARY_MOD:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left % right)

                elif op == OpCode.BINARY_POW:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left ** right)

                # ---- Augmented assignment ----
                elif op in (OpCode.AUG_ADD, OpCode.AUG_SUB, OpCode.AUG_MUL,
                            OpCode.AUG_DIV, OpCode.AUG_FLOOR_DIV,
                            OpCode.AUG_POW, OpCode.AUG_MOD):
                    name = code.names[arg]
                    operand = frame.pop()
                    current = frame.env.get(name)
                    aug_ops = {
                        OpCode.AUG_ADD: lambda a, b: a + b,
                        OpCode.AUG_SUB: lambda a, b: a - b,
                        OpCode.AUG_MUL: lambda a, b: a * b,
                        OpCode.AUG_DIV: lambda a, b: a / b,
                        OpCode.AUG_FLOOR_DIV: lambda a, b: a // b,
                        OpCode.AUG_POW: lambda a, b: a ** b,
                        OpCode.AUG_MOD: lambda a, b: a % b,
                    }
                    result = aug_ops[op](current, operand)
                    frame.env.set(name, result)

                # ---- Unary ----
                elif op == OpCode.UNARY_NEG:
                    frame.push(-frame.pop())

                elif op == OpCode.UNARY_POS:
                    frame.push(+frame.pop())

                elif op == OpCode.UNARY_NOT:
                    frame.push(not self._is_truthy(frame.pop()))

                # ---- Comparison ----
                elif op == OpCode.COMPARE_EQ:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left == right)

                elif op == OpCode.COMPARE_NE:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left != right)

                elif op == OpCode.COMPARE_LT:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left < right)

                elif op == OpCode.COMPARE_GT:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left > right)

                elif op == OpCode.COMPARE_LE:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left <= right)

                elif op == OpCode.COMPARE_GE:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left >= right)

                elif op == OpCode.COMPARE_IN:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left in right)

                elif op == OpCode.COMPARE_IS:
                    right = frame.pop()
                    left = frame.pop()
                    frame.push(left is right)

                # ---- Jumps ----
                elif op == OpCode.JUMP_ABSOLUTE:
                    frame.ip = arg

                elif op == OpCode.JUMP_IF_FALSE:
                    cond = frame.pop()
                    if not self._is_truthy(cond):
                        frame.ip = arg

                elif op == OpCode.JUMP_IF_TRUE:
                    cond = frame.pop()
                    if self._is_truthy(cond):
                        frame.ip = arg

                elif op == OpCode.JUMP_IF_FALSE_OR_POP:
                    # Short-circuit: if falsy, jump and keep value on stack
                    if not self._is_truthy(frame.peek()):
                        frame.ip = arg
                    else:
                        frame.pop()

                elif op == OpCode.JUMP_IF_TRUE_OR_POP:
                    if self._is_truthy(frame.peek()):
                        frame.ip = arg
                    else:
                        frame.pop()

                # ---- Loops ----
                elif op == OpCode.GET_ITER:
                    iterable = frame.pop()
                    frame.push(iter(iterable))

                elif op == OpCode.FOR_ITER:
                    iterator = frame.peek()
                    try:
                        value = next(iterator)
                        frame.push(value)
                    except StopIteration:
                        frame.pop()  # remove iterator
                        frame.ip = arg

                elif op == OpCode.BREAK_LOOP:
                    raise VMBreak()

                elif op == OpCode.CONTINUE_LOOP:
                    raise VMContinue(arg)

                # ---- Functions ----
                elif op == OpCode.MAKE_FUNCTION:
                    func_code = frame.pop()  # CodeObject
                    defaults = []
                    for _ in range(arg):
                        defaults.insert(0, frame.pop())
                    func = VMFunction(func_code.name, func_code, defaults, frame.env)
                    frame.push(func)

                elif op == OpCode.CALL_FUNCTION:
                    args = []
                    for _ in range(arg):
                        args.insert(0, frame.pop())
                    func = frame.pop()
                    result = self._call_function(func, args, {}, instr)
                    frame.push(result)

                elif op == OpCode.CALL_FUNCTION_KW:
                    kw_names = frame.pop()  # list of keyword names
                    kw_values = []
                    for _ in range(len(kw_names)):
                        kw_values.insert(0, frame.pop())
                    kwargs = dict(zip(kw_names, kw_values))
                    pos_args = []
                    for _ in range(arg):
                        pos_args.insert(0, frame.pop())
                    func = frame.pop()
                    result = self._call_function(func, pos_args, kwargs, instr)
                    frame.push(result)

                elif op == OpCode.RETURN_VALUE:
                    value = frame.pop()
                    raise VMReturn(value)

                # ---- Classes ----
                elif op == OpCode.MAKE_CLASS:
                    method_names = frame.pop()  # list of method names
                    class_name = frame.pop()  # class name string

                    methods = {}
                    class_vars = {}
                    items = []
                    for _ in range(arg):
                        items.insert(0, frame.pop())

                    for i, mname in enumerate(method_names):
                        if mname.startswith('__classvar__'):
                            var_name = mname[len('__classvar__'):]
                            class_vars[var_name] = items[i]
                        else:
                            # Convert VMFunction to KilatFunction-like for class methods
                            methods[mname] = items[i]

                    base_class = frame.pop()  # base class or None

                    if isinstance(base_class, str):
                        base_class = frame.env.get(base_class)

                    if base_class is not None and not isinstance(base_class, KilatClass):
                        base_class = None

                    klass = KilatClass(class_name, base_class, {})

                    # Create a class env for method closures
                    class_env = Environment(parent=frame.env)
                    for var_name, var_val in class_vars.items():
                        class_env.define(var_name, var_val)

                    # Re-wrap methods with class env as closure
                    for mname, mfunc in methods.items():
                        if isinstance(mfunc, VMFunction):
                            klass.methods[mname] = VMFunction(
                                mfunc.name, mfunc.code, mfunc.defaults, class_env
                            )
                        else:
                            klass.methods[mname] = mfunc

                    frame.push(klass)

                # ---- Collections ----
                elif op == OpCode.BUILD_LIST:
                    elements = []
                    for _ in range(arg):
                        elements.insert(0, frame.pop())
                    frame.push(elements)

                elif op == OpCode.BUILD_DICT:
                    pairs = []
                    for _ in range(arg):
                        val = frame.pop()
                        key = frame.pop()
                        pairs.insert(0, (key, val))
                    frame.push(dict(pairs))

                elif op == OpCode.BUILD_FSTRING:
                    parts = []
                    for _ in range(arg):
                        parts.insert(0, frame.pop())
                    frame.push(''.join(str(p) for p in parts))

                # ---- Exception handling ----
                elif op == OpCode.SETUP_TRY:
                    frame.try_stack.append(arg)  # handler address

                elif op == OpCode.POP_TRY:
                    if frame.try_stack:
                        frame.try_stack.pop()

                elif op == OpCode.RAISE:
                    exc_val = frame.pop()
                    raise KilatException(exc_val)

                elif op == OpCode.MATCH_EXCEPTION:
                    exc = frame.current_exception
                    if arg == -1:
                        # Bare except: always matches
                        frame.push(True)
                    else:
                        exc_type_name = code.names[arg]
                        if isinstance(exc, KilatException):
                            frame.push(True)
                        else:
                            try:
                                py_type = eval(exc_type_name)  # noqa: S307
                                frame.push(isinstance(exc, py_type))
                            except Exception:
                                frame.push(exc_type_name == type(exc).__name__)

                elif op == OpCode.END_FINALLY:
                    # Re-raise current exception if not handled
                    if frame.current_exception is not None:
                        exc = frame.current_exception
                        frame.current_exception = None
                        raise exc

                # ---- Imports ----
                elif op == OpCode.IMPORT_MODULE:
                    import importlib
                    module_name = code.names[arg]
                    try:
                        mod = importlib.import_module(module_name)
                        frame.push(mod)
                    except ImportError as e:
                        raise KilatRuntimeError(
                            f"Tidak dapat import '{module_name}': {e}", instr.line)

                elif op == OpCode.IMPORT_FROM:
                    mod = frame.peek()  # module on top of stack
                    attr_name = code.names[arg]
                    try:
                        frame.push(getattr(mod, attr_name))
                    except AttributeError:
                        raise KilatRuntimeError(
                            f"Import gagal: module has no attribute '{attr_name}'",
                            instr.line)

                # ---- Scope ----
                elif op == OpCode.DECLARE_GLOBAL:
                    name = code.names[arg]
                    frame.env.declare_global(name)

                else:
                    raise KilatRuntimeError(
                        f"Unknown opcode: {op}", instr.line)

            except VMReturn:
                raise
            except VMBreak:
                raise
            except VMContinue:
                raise
            except (KilatException, KilatRuntimeError) as exc:
                if frame.try_stack:
                    handler_addr = frame.try_stack.pop()
                    frame.current_exception = exc
                    frame.ip = handler_addr
                    # Clear the stack to the frame state before try
                    # (simplified: just continue from handler)
                else:
                    raise

        return None

    # ---------------------------------------------------------------- #
    #  Function calling                                                 #
    # ---------------------------------------------------------------- #

    def _call_function(self, func, args: list, kwargs: dict,
                       instr: Instruction) -> Any:
        if isinstance(func, VMFunction):
            return self._call_vm_function(func, args, kwargs, instr)

        if isinstance(func, KilatClass):
            return self._call_class(func, args, kwargs, instr)

        if callable(func):
            try:
                return func(*args, **kwargs)
            except TypeError as e:
                raise KilatRuntimeError(str(e), instr.line)

        raise KilatRuntimeError(f"Tidak boleh dipanggil: {func!r}", instr.line)

    def _call_vm_function(self, func: VMFunction, args: list, kwargs: dict,
                          instr: Instruction) -> Any:
        func_env = Environment(parent=func.closure)

        params = func.code.param_names
        required_count = func.code.param_count - len(func.defaults)

        # Bind positional arguments
        for i, val in enumerate(args):
            if i >= len(params):
                raise KilatRuntimeError(
                    f"Fungsi '{func.name}' menerima paling banyak "
                    f"{len(params)} argumen, diberi {len(args)}",
                    instr.line)
            func_env.define(params[i], val)

        # Bind keyword arguments
        for kw_name, kw_val in kwargs.items():
            if kw_name not in params:
                raise KilatRuntimeError(
                    f"Fungsi '{func.name}' tidak ada parameter '{kw_name}'",
                    instr.line)
            func_env.define(kw_name, kw_val)

        # Fill in defaults for unbound parameters
        for i in range(len(params)):
            if params[i] not in func_env.variables:
                default_index = i - required_count
                if default_index < 0 or default_index >= len(func.defaults):
                    raise KilatRuntimeError(
                        f"Fungsi '{func.name}' memerlukan argumen untuk '{params[i]}'",
                        instr.line)
                func_env.define(params[i], func.defaults[default_index])

        # Execute function body
        func_frame = Frame(func.code, func_env)
        try:
            self._execute_frame(func_frame)
            return None
        except VMReturn as ret:
            return ret.value

    def _call_class(self, klass: KilatClass, args: list, kwargs: dict,
                    instr: Instruction) -> KilatInstance:
        instance = KilatInstance(klass)
        init = klass._get_method('__init__')
        if init is not None:
            if isinstance(init, VMFunction):
                self._call_vm_function(init, [instance] + args, kwargs, instr)
            elif callable(init):
                init(instance, *args, **kwargs)
        return instance

    # ---------------------------------------------------------------- #
    #  Attribute access                                                 #
    # ---------------------------------------------------------------- #

    def _get_attribute(self, obj: Any, attr: str, frame: Frame) -> Any:
        if isinstance(obj, KilatInstance):
            if attr in obj.attributes:
                return obj.attributes[attr]
            method = obj.klass._get_method(attr)
            if method is not None:
                instance = obj
                vm = self
                if isinstance(method, VMFunction):
                    def bound_call(*args, **kwargs):
                        dummy_instr = Instruction(OpCode.NOP, 0, 0)
                        return vm._call_vm_function(method, [instance] + list(args),
                                                    kwargs, dummy_instr)
                    bound_call.__name__ = attr
                    return bound_call
                else:
                    def bound_call(*args, **kwargs):
                        return method(instance, *args, **kwargs)
                    bound_call.__name__ = attr
                    return bound_call
            raise KilatRuntimeError(f"Atribut '{attr}' tidak ditemui pada {obj.klass.name}")

        if isinstance(obj, KilatClass):
            method = obj._get_method(attr)
            if method is not None:
                return method
            raise KilatRuntimeError(f"Kelas '{obj.name}' tidak mempunyai atribut '{attr}'")

        try:
            return getattr(obj, attr)
        except AttributeError:
            raise KilatRuntimeError(
                f"Atribut '{attr}' tidak ditemui pada {type(obj).__name__}")

    # ---------------------------------------------------------------- #
    #  Truthiness                                                       #
    # ---------------------------------------------------------------- #

    def _is_truthy(self, value: Any) -> bool:
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

def run_bytecode(source: str, filename: str = '<kilat>'):
    """Parse, compile, and execute Kilat source via bytecode VM."""
    from kilat_compiler import compile_kilat
    code = compile_kilat(source, filename)
    vm = KilatVM()
    vm.run(code)
