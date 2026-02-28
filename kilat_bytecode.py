"""
Kilat-Lang Bytecode Definitions
Opcodes, CodeObject, and .klc serialization format.
"""

from enum import IntEnum
import struct
import json


# ------------------------------------------------------------------ #
#  Opcodes                                                             #
# ------------------------------------------------------------------ #

class OpCode(IntEnum):
    """Bytecode instruction opcodes for the Kilat VM."""

    # Stack manipulation
    NOP = 0
    POP_TOP = 1
    DUP_TOP = 2
    ROT_TWO = 3

    # Constants
    LOAD_CONST = 10        # arg: index into constants pool

    # Names (variables)
    LOAD_NAME = 20         # arg: index into names list
    STORE_NAME = 21        # arg: index into names list
    LOAD_GLOBAL = 22       # arg: index into names list
    STORE_GLOBAL = 23      # arg: index into names list
    DELETE_NAME = 24       # arg: index into names list
    STORE_NAME_DEFINE = 25 # arg: index into names — always define in current scope (for =)

    # Attributes
    LOAD_ATTR = 30         # arg: index into names (attribute name)
    STORE_ATTR = 31        # arg: index into names (attribute name)

    # Indexing
    LOAD_INDEX = 35
    STORE_INDEX = 36
    DELETE_INDEX = 37

    # Arithmetic (binary)
    BINARY_ADD = 40
    BINARY_SUB = 41
    BINARY_MUL = 42
    BINARY_DIV = 43
    BINARY_FLOOR_DIV = 44
    BINARY_MOD = 45
    BINARY_POW = 46

    # Augmented assignment: stack has value on top, reads/writes name at arg
    AUG_ADD = 50           # arg: name index
    AUG_SUB = 51
    AUG_MUL = 52
    AUG_DIV = 53
    AUG_FLOOR_DIV = 54
    AUG_POW = 55
    AUG_MOD = 56

    # Unary
    UNARY_NEG = 60
    UNARY_POS = 61
    UNARY_NOT = 62

    # Comparison
    COMPARE_EQ = 70
    COMPARE_NE = 71
    COMPARE_LT = 72
    COMPARE_GT = 73
    COMPARE_LE = 74
    COMPARE_GE = 75
    COMPARE_IN = 76
    COMPARE_IS = 77

    # Jumps
    JUMP_ABSOLUTE = 80     # arg: target instruction index
    JUMP_IF_FALSE = 81     # arg: target (pops condition)
    JUMP_IF_TRUE = 82      # arg: target (pops condition)
    JUMP_IF_FALSE_OR_POP = 83  # short-circuit: if falsy, jump & keep value; else pop
    JUMP_IF_TRUE_OR_POP = 84   # short-circuit: if truthy, jump & keep value; else pop

    # Loops
    GET_ITER = 90
    FOR_ITER = 91          # arg: jump target when iterator exhausted
    BREAK_LOOP = 92
    CONTINUE_LOOP = 93     # arg: jump target (loop start)

    # Functions
    MAKE_FUNCTION = 100    # arg: number of default values on stack
    CALL_FUNCTION = 101    # arg: number of positional arguments
    CALL_FUNCTION_KW = 102 # arg: number of positional args (kw names tuple on stack)
    RETURN_VALUE = 103

    # Classes
    MAKE_CLASS = 110       # arg: number of methods

    # Collections
    BUILD_LIST = 120       # arg: number of elements
    BUILD_DICT = 121       # arg: number of key-value pairs

    # F-strings
    BUILD_FSTRING = 125    # arg: number of parts

    # Exception handling
    SETUP_TRY = 130        # arg: handler address
    POP_TRY = 131
    RAISE = 132
    END_FINALLY = 133
    MATCH_EXCEPTION = 134  # arg: exception type name index (or -1 for bare except)

    # Imports
    IMPORT_MODULE = 140    # arg: module name index in names
    IMPORT_FROM = 141      # arg: name index (attribute to import)

    # Tuples
    BUILD_TUPLE = 126      # arg: number of elements

    # Slicing
    BUILD_SLICE = 127      # arg: number of components (2 or 3)

    # Scope
    DECLARE_GLOBAL = 150   # arg: name index

    # Unpacking
    UNPACK_SEQUENCE = 160  # arg: number of targets


# ------------------------------------------------------------------ #
#  Instruction                                                         #
# ------------------------------------------------------------------ #

class Instruction:
    """A single bytecode instruction."""
    __slots__ = ('opcode', 'arg', 'line')

    def __init__(self, opcode: OpCode, arg: int = 0, line: int = 0):
        self.opcode = opcode
        self.arg = arg
        self.line = line

    def __repr__(self):
        name = OpCode(self.opcode).name
        if self.arg != 0:
            return f"{name}({self.arg})"
        return name


# ------------------------------------------------------------------ #
#  CodeObject                                                          #
# ------------------------------------------------------------------ #

class CodeObject:
    """Compiled bytecode for a module, function, or class body."""

    def __init__(self, name: str = '<module>'):
        self.name: str = name
        self.constants: list = []       # constant pool
        self.names: list = []           # variable / attribute name strings
        self.instructions: list = []    # list of Instruction objects
        self.param_count: int = 0       # number of parameters (for functions)
        self.param_names: list = []     # parameter name strings
        self.var_args: str = None       # *args parameter name (or None)
        self.kw_args: str = None        # **kwargs parameter name (or None)

    # -- helpers for building --

    def add_constant(self, value) -> int:
        """Add a constant and return its index. Reuses existing entries."""
        # Don't deduplicate CodeObjects or complex types
        if not isinstance(value, (CodeObject, list, dict)):
            for i, c in enumerate(self.constants):
                if type(c) is type(value) and c == value:
                    return i
        idx = len(self.constants)
        self.constants.append(value)
        return idx

    def add_name(self, name: str) -> int:
        """Add a name and return its index. Reuses existing entries."""
        try:
            return self.names.index(name)
        except ValueError:
            idx = len(self.names)
            self.names.append(name)
            return idx

    def emit(self, opcode: OpCode, arg: int = 0, line: int = 0) -> int:
        """Emit an instruction, return its index."""
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, arg, line))
        return idx

    def current_offset(self) -> int:
        """Return the index where the next instruction will be emitted."""
        return len(self.instructions)

    def patch_jump(self, instr_index: int, target: int = None):
        """Patch a jump instruction's arg to point to target (or current offset)."""
        if target is None:
            target = self.current_offset()
        self.instructions[instr_index].arg = target

    def disassemble(self) -> str:
        """Return a human-readable disassembly."""
        lines = [f"=== CodeObject '{self.name}' ==="]
        lines.append(f"  params: {self.param_names} (count={self.param_count})")
        lines.append(f"  constants: {self.constants}")
        lines.append(f"  names: {self.names}")
        lines.append("  instructions:")
        for i, instr in enumerate(self.instructions):
            extra = ""
            if instr.opcode in (OpCode.LOAD_CONST,) and instr.arg < len(self.constants):
                c = self.constants[instr.arg]
                if isinstance(c, CodeObject):
                    extra = f"  ; <code '{c.name}'>"
                else:
                    extra = f"  ; {c!r}"
            elif instr.opcode in (OpCode.LOAD_NAME, OpCode.STORE_NAME,
                                   OpCode.STORE_NAME_DEFINE,
                                   OpCode.LOAD_GLOBAL, OpCode.STORE_GLOBAL,
                                   OpCode.LOAD_ATTR, OpCode.STORE_ATTR,
                                   OpCode.DELETE_NAME, OpCode.DECLARE_GLOBAL,
                                   OpCode.AUG_ADD, OpCode.AUG_SUB, OpCode.AUG_MUL,
                                   OpCode.AUG_DIV, OpCode.AUG_FLOOR_DIV,
                                   OpCode.AUG_POW, OpCode.AUG_MOD,
                                   OpCode.IMPORT_MODULE, OpCode.IMPORT_FROM):
                if instr.arg < len(self.names):
                    extra = f"  ; '{self.names[instr.arg]}'"
            line_info = f"[L{instr.line}]" if instr.line else ""
            lines.append(f"    {i:4d}  {OpCode(instr.opcode).name:<25s} {instr.arg:<6d}{extra} {line_info}")
        return '\n'.join(lines)


# ------------------------------------------------------------------ #
#  Serialization (.klc format)                                         #
# ------------------------------------------------------------------ #

KLC_MAGIC = b'KLC\x00'
KLC_VERSION = (1, 0)

# Type tags for serialization
_TAG_NONE = 0
_TAG_INT = 1
_TAG_FLOAT = 2
_TAG_STRING = 3
_TAG_BOOL_TRUE = 4
_TAG_BOOL_FALSE = 5
_TAG_CODE = 6
_TAG_LIST = 7


def serialize_code(code: CodeObject) -> bytes:
    """Serialize a CodeObject to bytes for .klc files."""
    buf = bytearray()
    buf.extend(KLC_MAGIC)
    buf.extend(struct.pack('BB', *KLC_VERSION))
    _serialize_code_obj(buf, code)
    return bytes(buf)


def _serialize_string(buf: bytearray, s: str):
    encoded = s.encode('utf-8')
    buf.extend(struct.pack('<I', len(encoded)))
    buf.extend(encoded)


def _serialize_value(buf: bytearray, value):
    """Serialize a constant value."""
    if value is None:
        buf.append(_TAG_NONE)
    elif isinstance(value, bool):
        buf.append(_TAG_BOOL_TRUE if value else _TAG_BOOL_FALSE)
    elif isinstance(value, int):
        buf.append(_TAG_INT)
        buf.extend(struct.pack('<q', value))
    elif isinstance(value, float):
        buf.append(_TAG_FLOAT)
        buf.extend(struct.pack('<d', value))
    elif isinstance(value, str):
        buf.append(_TAG_STRING)
        _serialize_string(buf, value)
    elif isinstance(value, CodeObject):
        buf.append(_TAG_CODE)
        _serialize_code_obj(buf, value)
    elif isinstance(value, list):
        buf.append(_TAG_LIST)
        buf.extend(struct.pack('<I', len(value)))
        for item in value:
            _serialize_value(buf, item)
    else:
        # Fallback: serialize as string repr
        buf.append(_TAG_STRING)
        _serialize_string(buf, repr(value))


def _serialize_code_obj(buf: bytearray, code: CodeObject):
    # Name
    _serialize_string(buf, code.name)
    # Param count + param names
    buf.extend(struct.pack('<I', code.param_count))
    buf.extend(struct.pack('<I', len(code.param_names)))
    for pn in code.param_names:
        _serialize_string(buf, pn)
    # var_args / kw_args
    _serialize_string(buf, code.var_args or '')
    _serialize_string(buf, code.kw_args or '')
    # Constants
    buf.extend(struct.pack('<I', len(code.constants)))
    for c in code.constants:
        _serialize_value(buf, c)
    # Names
    buf.extend(struct.pack('<I', len(code.names)))
    for n in code.names:
        _serialize_string(buf, n)
    # Instructions
    buf.extend(struct.pack('<I', len(code.instructions)))
    for instr in code.instructions:
        buf.extend(struct.pack('<BhH', instr.opcode, instr.arg, instr.line))


def deserialize_code(data: bytes) -> CodeObject:
    """Deserialize a .klc file to a CodeObject."""
    if data[:4] != KLC_MAGIC:
        raise ValueError("Invalid .klc file (bad magic)")
    major, minor = struct.unpack('BB', data[4:6])
    if (major, minor) != KLC_VERSION:
        raise ValueError(f"Unsupported .klc version {major}.{minor}")
    offset = [6]  # mutable offset for recursive parsing
    return _deserialize_code_obj(data, offset)


def _read_bytes(data: bytes, offset: list, n: int) -> bytes:
    result = data[offset[0]:offset[0] + n]
    offset[0] += n
    return result


def _read_string(data: bytes, offset: list) -> str:
    length = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    return _read_bytes(data, offset, length).decode('utf-8')


def _read_value(data: bytes, offset: list):
    tag = data[offset[0]]
    offset[0] += 1
    if tag == _TAG_NONE:
        return None
    elif tag == _TAG_BOOL_TRUE:
        return True
    elif tag == _TAG_BOOL_FALSE:
        return False
    elif tag == _TAG_INT:
        val = struct.unpack('<q', _read_bytes(data, offset, 8))[0]
        return val
    elif tag == _TAG_FLOAT:
        val = struct.unpack('<d', _read_bytes(data, offset, 8))[0]
        return val
    elif tag == _TAG_STRING:
        return _read_string(data, offset)
    elif tag == _TAG_CODE:
        return _deserialize_code_obj(data, offset)
    elif tag == _TAG_LIST:
        count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
        return [_read_value(data, offset) for _ in range(count)]
    else:
        raise ValueError(f"Unknown constant tag: {tag}")


def _deserialize_code_obj(data: bytes, offset: list) -> CodeObject:
    code = CodeObject()
    code.name = _read_string(data, offset)
    code.param_count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    pn_count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    code.param_names = [_read_string(data, offset) for _ in range(pn_count)]
    # var_args / kw_args
    va = _read_string(data, offset)
    code.var_args = va if va else None
    ka = _read_string(data, offset)
    code.kw_args = ka if ka else None
    # Constants
    c_count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    code.constants = [_read_value(data, offset) for _ in range(c_count)]
    # Names
    n_count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    code.names = [_read_string(data, offset) for _ in range(n_count)]
    # Instructions
    i_count = struct.unpack('<I', _read_bytes(data, offset, 4))[0]
    code.instructions = []
    for _ in range(i_count):
        raw = _read_bytes(data, offset, 5)
        op, arg, line = struct.unpack('<BhH', raw)
        code.instructions.append(Instruction(OpCode(op), arg, line))
    return code
