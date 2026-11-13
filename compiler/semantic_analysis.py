"""
Phase 3: Semantic Analysis

Input : the AST (`ast_nodes.Program`) produced by `syntax_analysis.parse`
Output: the same AST, annotated in place (see "Annotations" below)
Errors: raises `SemanticAnalysisError`, which carries *every* error found (not just the first)

Checks performed
    1. Duplicate declaration in the same scope
    2. Use of an undeclared variable (searching enclosing scopes)
    3. Reading a variable that is not definitely initialized
    4. Type compatibility on declarations with an initializer and on assignments
    5. '+', '-', '*', '/' and unary '-' need int operands
    6. 'if' conditions must be bool
    7. Division by the literal 0

AST attributes this file reads (rename here if your ast_nodes.py differs):
    Program.statements          Block.statements
    VarDecl.name / .var_type / .initializer
    Assignment.name / .value
    LogStatement.expression
    IfStatement.condition / .then_block / .else_block
    BinaryOp.op / .left / .right        UnaryOp.op / .operand
    IntLiteral / StringLiteral / BoolLiteral .value
    Identifier.name

Annotations added for the code generator (Phase 4)
    every expression node     .inferred_type   "int" | "bool" | "str"
    VarDecl / Assignment / Identifier   .symbol   a Symbol (use symbol.unique_name as the
                                                  variable name in TAC, so a shadowed `x`
                                                  in an inner block never clashes with an
                                                  outer `x`)

Scoping rules: blocks `{}` open a new scope. Shadowing an outer variable in an inner block
is allowed; declaring the same name twice in the *same* scope is an error.

Initialization rules: a variable is "definitely initialized" if every path to the read
assigns it. Assigning only inside the `if` branch (or in just one of if/else) does not count.
"""

from typing import Dict, List, Optional, Set

from .ast_nodes import (
  Assignment, BinaryOp, Block, BoolLiteral, Identifier, IfStatement,
  IntLiteral, LogStatement, Program, StringLiteral, UnaryOp, VarDecl,
)

INT, BOOL, STR = "int", "bool", "str"

# Internal marker for "this expression already produced an error". It makes the other checks
# stay quiet about it, so one mistake does not trigger a cascade of follow-up errors.
ERROR = "<error>"

TYPE_NAMES = {INT: "int", BOOL: "bool", STR: "str"}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SemanticError:
  """One semantic problem, with an optional source position."""

  def __init__(self, message, line=None, column=None):
    self.message = message
    self.line = line
    self.column = column

  def __str__(self):
    if self.line is None:
      return f"Semantic Error: {self.message}"
    if self.column is None:
      return f"Semantic Error at line {self.line}: {self.message}"
    return f"Semantic Error at line {self.line}, column {self.column}: {self.message}"

  __repr__ = __str__


class SemanticAnalysisError(Exception):
  """Raised by `analyze` when one or more semantic errors were found."""

  def __init__(self, errors: List[SemanticError]):
    self.errors = errors
    super().__init__("\n".join(str(e) for e in errors))


# ---------------------------------------------------------------------------
# Symbols and scopes
# ---------------------------------------------------------------------------

class Symbol:
  def __init__(self, name, type_, unique_name, line=None):
    self.name = name
    self.type = type_
    self.unique_name = unique_name
    self.line = line  # where it was declared

  def __repr__(self):
    return f"Symbol({self.name}: {self.type} -> {self.unique_name})"


class Analyzer:
  def __init__(self):
    self.scopes: List[Dict[str, Symbol]] = [{}]
    self.errors: List[SemanticError] = []
    # Symbols that are definitely initialized at the current point of the walk.
    self.initialized: Set[Symbol] = set()
    self._name_counts: Dict[str, int] = {}

  # ----- helpers -----------------------------------------------------------

  def _error(self, message, node):
    self.errors.append(
      SemanticError(message, getattr(node, "line", None), getattr(node, "column", None)))

  def _lookup(self, name) -> Optional[Symbol]:
    for scope in reversed(self.scopes):
      if name in scope:
        return scope[name]
    return None

  def _declare(self, name, type_, node) -> Optional[Symbol]:
    """Add `name` to the innermost scope. Returns None (and reports) on a duplicate."""
    current = self.scopes[-1]
    if name in current:
      previous = current[name]
      where = f" (first declared at line {previous.line})" if previous.line is not None else ""
      self._error(f"variable '{name}' is already declared in this scope{where}", node)
      return None

    count = self._name_counts.get(name, 0)
    self._name_counts[name] = count + 1
    unique = name if count == 0 else f"{name}_{count}"

    symbol = Symbol(name, type_, unique, getattr(node, "line", None))
    current[name] = symbol
    return symbol

  # ----- visitor dispatch --------------------------------------------------

  def visit(self, node):
    method = getattr(self, f"visit_{type(node).__name__}", None)
    if method is None:
      raise NotImplementedError(f"semantic analysis has no rule for {type(node).__name__}")
    return method(node)

  # ----- statements --------------------------------------------------------

  def visit_Program(self, node: Program):
    for statement in node.statements:
      self.visit(statement)

  def visit_Block(self, node: Block):
    self.scopes.append({})
    for statement in node.statements:
      self.visit(statement)
    self.scopes.pop()

  def visit_VarDecl(self, node: VarDecl):
    # Check the initializer BEFORE declaring the name, so `dec x : int = x;` reports x as
    # undeclared instead of reading itself.
    init_type = None
    if node.initializer is not None:
      init_type = self.visit(node.initializer)

    symbol = self._declare(node.name, node.var_type, node)
    node.symbol = symbol

    if node.initializer is None or symbol is None:
      return

    if init_type != ERROR and init_type != node.var_type:
      self._error(
        f"cannot initialize '{node.name}' of type {node.var_type} with a value of type {init_type}",
        node)
    self.initialized.add(symbol)

  def visit_Assignment(self, node: Assignment):
    value_type = self.visit(node.value)

    symbol = self._lookup(node.name)
    node.symbol = symbol
    if symbol is None:
      self._error(f"assignment to undeclared variable '{node.name}'", node)
      return

    if value_type != ERROR and value_type != symbol.type:
      self._error(
        f"cannot assign a value of type {value_type} to '{node.name}' (declared as {symbol.type})",
        node)
    self.initialized.add(symbol)

  def visit_LogStatement(self, node: LogStatement):
    self.visit(node.expression)  # any type can be logged

  def visit_IfStatement(self, node: IfStatement):
    cond_type = self.visit(node.condition)
    if cond_type != ERROR and cond_type != BOOL:
      self._error(f"'if' condition must be bool, but found {cond_type}", node.condition)

    before = set(self.initialized)

    self.visit(node.then_block)
    after_then = self.initialized

    self.initialized = set(before)
    if node.else_block is not None:
      self.visit(node.else_block)
    after_else = self.initialized

    # Only what BOTH paths initialized is safe to read afterwards.
    self.initialized = after_then & after_else

  # ----- expressions (each returns the expression's type) ------------------

  def _typed(self, node, type_):
    node.inferred_type = type_
    return type_

  def visit_IntLiteral(self, node: IntLiteral):
    return self._typed(node, INT)

  def visit_StringLiteral(self, node: StringLiteral):
    return self._typed(node, STR)

  def visit_BoolLiteral(self, node: BoolLiteral):
    return self._typed(node, BOOL)

  def visit_Identifier(self, node: Identifier):
    symbol = self._lookup(node.name)
    node.symbol = symbol
    if symbol is None:
      self._error(f"use of undeclared variable '{node.name}'", node)
      return self._typed(node, ERROR)

    if symbol not in self.initialized:
      self._error(f"variable '{node.name}' may be used before it is assigned a value", node)
    return self._typed(node, symbol.type)

  def visit_UnaryOp(self, node: UnaryOp):
    operand_type = self.visit(node.operand)
    if operand_type == ERROR:
      return self._typed(node, ERROR)
    if operand_type != INT:
      self._error(f"operator '{node.op}' needs an int operand, but found {operand_type}", node)
      return self._typed(node, ERROR)
    return self._typed(node, INT)

  def visit_BinaryOp(self, node: BinaryOp):
    left = self.visit(node.left)
    right = self.visit(node.right)

    if left == ERROR or right == ERROR:
      return self._typed(node, ERROR)

    if left != INT or right != INT:
      self._error(
        f"operator '{node.op}' needs int operands, but found {left} and {right}", node)
      return self._typed(node, ERROR)

    if node.op == "/" and isinstance(node.right, IntLiteral) and node.right.value == 0:
      self._error("division by zero", node)

    return self._typed(node, INT)


# ---------------------------------------------------------------------------
# Convenience function (mirrors `lex(code)` and `parse(tokens)`)
# ---------------------------------------------------------------------------

def analyze(program: Program) -> Program:
  """
  Run semantic analysis on an AST. Returns the same (annotated) AST, or raises
  SemanticAnalysisError holding every error found.
  """
  analyzer = Analyzer()
  analyzer.visit(program)
  if analyzer.errors:
    raise SemanticAnalysisError(analyzer.errors)
  return program
