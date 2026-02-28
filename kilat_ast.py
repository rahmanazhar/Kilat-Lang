"""
Kilat-Lang AST (Abstract Syntax Tree)
Defines all node types for the language
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


# Base classes
class ASTNode:
    """Base class for all AST nodes"""
    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column


# Literals
@dataclass
class NumberNode(ASTNode):
    value: Union[int, float]
    line: int = 0
    column: int = 0


@dataclass
class StringNode(ASTNode):
    value: str
    line: int = 0
    column: int = 0


@dataclass
class BooleanNode(ASTNode):
    value: bool
    line: int = 0
    column: int = 0


@dataclass
class NoneNode(ASTNode):
    line: int = 0
    column: int = 0


@dataclass
class IdentifierNode(ASTNode):
    name: str
    line: int = 0
    column: int = 0


# F-strings: list of parts (StringNode literals and expression nodes)
@dataclass
class FStringNode(ASTNode):
    parts: List[ASTNode]  # alternating StringNode (literal) and expression nodes
    line: int = 0
    column: int = 0


# Collections
@dataclass
class ListNode(ASTNode):
    elements: List[ASTNode]
    line: int = 0
    column: int = 0


@dataclass
class DictNode(ASTNode):
    pairs: List[tuple]  # List of (key, value) tuples
    line: int = 0
    column: int = 0


# Binary operations
@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str  # +, -, *, /, //, %, **, ==, !=, <, >, <=, >=, dan, atau_logik
    right: ASTNode
    line: int = 0
    column: int = 0


# Unary operations
@dataclass
class UnaryOpNode(ASTNode):
    operator: str  # -, bukan
    operand: ASTNode
    line: int = 0
    column: int = 0


# Variable operations
@dataclass
class AssignmentNode(ASTNode):
    target: str
    value: ASTNode
    line: int = 0
    column: int = 0


@dataclass
class AugmentedAssignmentNode(ASTNode):
    """Augmented assignment: +=, -=, *=, /=, //=, **=, %="""
    target: str        # variable name (or index/attr target string)
    operator: str      # '+', '-', '*', '/', '//', '**', '%'
    value: ASTNode
    line: int = 0
    column: int = 0


@dataclass
class IndexAssignmentNode(ASTNode):
    """Index assignment: list[i] = value  or  dict['key'] = value"""
    object: ASTNode
    index: ASTNode
    value: ASTNode
    line: int = 0
    column: int = 0


@dataclass
class AttributeNode(ASTNode):
    object: ASTNode
    attribute: str
    line: int = 0
    column: int = 0


@dataclass
class AttributeAssignmentNode(ASTNode):
    object: ASTNode
    attribute: str
    value: ASTNode
    line: int = 0
    column: int = 0


@dataclass
class IndexNode(ASTNode):
    object: ASTNode
    index: ASTNode
    line: int = 0
    column: int = 0


# Control flow
@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    elif_parts: List[tuple]  # List of (condition, body) tuples
    else_body: Optional[List[ASTNode]] = None
    line: int = 0
    column: int = 0


@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: List[ASTNode]
    line: int = 0
    column: int = 0


@dataclass
class ForNode(ASTNode):
    variable: str
    iterable: ASTNode
    body: List[ASTNode]
    variables: Optional[List[str]] = None  # for tuple unpacking: untuk diulang i, v dalam ...
    line: int = 0
    column: int = 0


@dataclass
class BreakNode(ASTNode):
    line: int = 0
    column: int = 0


@dataclass
class ContinueNode(ASTNode):
    line: int = 0
    column: int = 0


@dataclass
class ReturnNode(ASTNode):
    value: Optional[ASTNode] = None
    line: int = 0
    column: int = 0


# Functions
@dataclass
class FunctionDefNode(ASTNode):
    name: str
    parameters: List[str]
    defaults: List[ASTNode]  # Default values for parameters
    body: List[ASTNode]
    var_args: Optional[str] = None      # *args parameter name
    kw_args: Optional[str] = None       # **kwargs parameter name
    decorators: List[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0


@dataclass
class FunctionCallNode(ASTNode):
    function: Union[str, ASTNode]       # Function name or expression
    arguments: List[ASTNode]
    keyword_args: Dict[str, ASTNode]    # Keyword arguments  {name: expr}
    line: int = 0
    column: int = 0


# Classes
@dataclass
class ClassDefNode(ASTNode):
    name: str
    base_class: Optional[str]
    body: List[ASTNode]
    decorators: List[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0


# Exception handling
@dataclass
class TryNode(ASTNode):
    try_body: List[ASTNode]
    except_clauses: List[tuple]  # List of (exception_type, alias, body) tuples
    finally_body: Optional[List[ASTNode]] = None
    line: int = 0
    column: int = 0


@dataclass
class RaiseNode(ASTNode):
    exception: ASTNode
    line: int = 0
    column: int = 0


# Program
@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]
    line: int = 0
    column: int = 0


# Import statements
@dataclass
class ImportNode(ASTNode):
    module: str
    alias: Optional[str] = None
    line: int = 0
    column: int = 0


@dataclass
class FromImportNode(ASTNode):
    module: str
    names: List[str]
    aliases: List[Optional[str]]
    line: int = 0
    column: int = 0


# Global / nonlocal
@dataclass
class GlobalNode(ASTNode):
    names: List[str]
    line: int = 0
    column: int = 0


@dataclass
class NonlocalNode(ASTNode):
    names: List[str]
    line: int = 0
    column: int = 0


# Delete statement
@dataclass
class DeleteNode(ASTNode):
    target: ASTNode
    line: int = 0
    column: int = 0


# Pass statement (as a real node, not None)
@dataclass
class PassNode(ASTNode):
    line: int = 0
    column: int = 0


# Slicing: obj[start:stop:step]
@dataclass
class SliceNode(ASTNode):
    start: Optional[ASTNode]    # None if omitted
    stop: Optional[ASTNode]     # None if omitted
    step: Optional[ASTNode]     # None if omitted
    line: int = 0
    column: int = 0


# List comprehension: [expr untuk diulang var dalam iterable jika condition]
@dataclass
class ListCompNode(ASTNode):
    expression: ASTNode
    variable: str
    iterable: ASTNode
    condition: Optional[ASTNode] = None
    variables: Optional[List[str]] = None  # for tuple unpacking
    line: int = 0
    column: int = 0


# Lambda expression: lambda params: expr
@dataclass
class LambdaNode(ASTNode):
    parameters: List[str]
    defaults: List[ASTNode]
    body: ASTNode               # single expression
    line: int = 0
    column: int = 0


# Ternary expression: true_value jika condition atau false_value
@dataclass
class TernaryNode(ASTNode):
    true_value: ASTNode
    condition: ASTNode
    false_value: ASTNode
    line: int = 0
    column: int = 0


# Tuple literal: (a, b, c)
@dataclass
class TupleNode(ASTNode):
    elements: List[ASTNode]
    line: int = 0
    column: int = 0


# Multiple assignment / tuple unpacking: a, b = 1, 2
@dataclass
class MultiAssignmentNode(ASTNode):
    targets: List[str]          # variable names
    value: ASTNode              # right-hand side
    line: int = 0
    column: int = 0


# With statement: dengan expr sebagai var:
@dataclass
class WithNode(ASTNode):
    context_expr: ASTNode
    alias: Optional[str]
    body: List[ASTNode]
    line: int = 0
    column: int = 0


# Yield expression: berikan value
@dataclass
class YieldNode(ASTNode):
    value: Optional[ASTNode] = None
    line: int = 0
    column: int = 0
