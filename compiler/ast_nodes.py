"""
STAND-IN ast_nodes.py -- for testing only.

Reconstructed from how syntax_analysis.py calls each constructor. If your teammate
already has the real ast_nodes.py, use theirs and only check that the attribute names
match what semantic_analysis.py reads (listed at the top of that file).
"""


class Node:
  line = None
  column = None


class Program(Node):
  def __init__(self, statements):
    self.statements = statements


class VarDecl(Node):
  def __init__(self, name, var_type, initializer=None):
    self.name = name
    self.var_type = var_type
    self.initializer = initializer


class Assignment(Node):
  def __init__(self, name, value):
    self.name = name
    self.value = value


class LogStatement(Node):
  def __init__(self, expression):
    self.expression = expression


class IfStatement(Node):
  def __init__(self, condition, then_block, else_block=None):
    self.condition = condition
    self.then_block = then_block
    self.else_block = else_block


class Block(Node):
  def __init__(self, statements):
    self.statements = statements


class BinaryOp(Node):
  def __init__(self, op, left, right):
    self.op = op
    self.left = left
    self.right = right


class UnaryOp(Node):
  def __init__(self, op, operand):
    self.op = op
    self.operand = operand


class IntLiteral(Node):
  def __init__(self, value):
    self.value = value


class StringLiteral(Node):
  def __init__(self, value):
    self.value = value


class BoolLiteral(Node):
  def __init__(self, value):
    self.value = value


class Identifier(Node):
  def __init__(self, name):
    self.name = name
