"""
AST node definitions for our toy language.

This module is the "contract" between Phase 2 (Syntax Analysis), which BUILDS the
tree, and Phases 3 and 4 (Semantic Analysis, Code Generation), which READ it.

Design notes
------------
* Every node is a plain @dataclass, so nodes are easy to construct, print, and
  compare in tests.
* Every node also carries `line` and `column` (1-based, or None if the lexer did
  not provide positions). The Semantic Analyzer can use these to report
  errors like "line 4: cannot add int and str".
* Parentheses do not get their own node: the tree shape already encodes grouping.
* Operators are stored as their source text: "+", "-", "*", "/".
* `var_type` is stored as the source text: "int", "bool" or "str".
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import List, Optional, Union


class Node:
  """Base class of every AST node. Holds the source position of the node."""
  line: Optional[int] = None
  column: Optional[int] = None


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass
class IntLiteral(Node):
  value: int                      # e.g. 42


@dataclass
class StringLiteral(Node):
  value: str                      # quotes already stripped: "hi" -> hi


@dataclass
class BoolLiteral(Node):
  value: bool                     # True / False


@dataclass
class Identifier(Node):
  name: str                       # a variable being READ, e.g. the x in x + 1


@dataclass
class UnaryOp(Node):
  operator: str                   # currently only "-"
  operand: Expression


@dataclass
class BinaryOp(Node):
  operator: str                   # "+", "-", "*" or "/"
  left: Expression
  right: Expression


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class VarDecl(Node):
  """dec x : int;   or   dec x : int = 5;"""
  name: str
  var_type: str                   # "int" | "bool" | "str"
  initializer: Optional[Expression] = None


@dataclass
class Assignment(Node):
  """x = expression;"""
  name: str                       # the variable being WRITTEN
  value: Expression


@dataclass
class LogStatement(Node):
  """log(expression);"""
  expression: Expression


@dataclass
class Block(Node):
  """{ statement* }  -- a new scope in Java-style brace scoping."""
  statements: List[Statement]


@dataclass
class IfStatement(Node):
  """if condition { ... }   or   if condition { ... } else { ... }"""
  condition: Expression
  then_block: Block
  else_block: Optional[Block] = None


@dataclass
class Program(Node):
  """Root of the tree: the whole source file."""
  statements: List[Statement]


# Convenient type aliases (used in the annotations above).
Expression = Union[IntLiteral, StringLiteral, BoolLiteral, Identifier, UnaryOp, BinaryOp]
Statement = Union[VarDecl, Assignment, LogStatement, IfStatement]


# ---------------------------------------------------------------------------
# Helpers for the rest of the team
# ---------------------------------------------------------------------------

class NodeVisitor:
  """
  Base class for walking the AST (useful for Semantic Analysis / Code Generation).

  Define a method called visit_<NodeClassName> for each node you care about:

      class TypeChecker(NodeVisitor):
        def visit_BinaryOp(self, node):
          left = self.visit(node.left)
          right = self.visit(node.right)
          ...

  Nodes without a matching method fall back to `generic_visit`, which simply
  visits all child nodes.
  """

  def visit(self, node):
    method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
    return method(node)

  def generic_visit(self, node):
    for f in fields(node):
      value = getattr(node, f.name)
      if isinstance(value, Node):
        self.visit(value)
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, Node):
            self.visit(item)


def dump(node, indent=0):
  """Return an indented, human-readable string of the tree (great for demos and debugging)."""
  pad = "  " * indent
  scalars, children = [], []

  for f in fields(node):
    value = getattr(node, f.name)
    if isinstance(value, (Node, list)):
      children.append((f.name, value))
    elif value is not None:
      scalars.append(f"{f.name}={value!r}")

  header = type(node).__name__ + (" " + " ".join(scalars) if scalars else "")
  lines = [pad + header]
  for name, value in children:
    lines.append(f"{pad}  {name}:")
    for item in (value if isinstance(value, list) else [value]):
      lines.append(dump(item, indent + 2))
  return "\n".join(lines)