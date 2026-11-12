"""
Phase 2: Syntax Analysis (Recursive Descent Parser)

Input : the list of Token objects produced by `lexical_analysis.lex`
Output: an Abstract Syntax Tree (`ast_nodes.Program`)
Errors: raises `SyntaxAnalysisError` on the first syntax error found

Grammar (EBNF). Terminals in quotes are KEYWORD/punctuation tokens, names in
CAPITALS are token types produced by the lexer.

    program     -> statement* EOF
    statement   -> declaration | assignment | log_stmt | if_stmt
    declaration -> "dec" IDENTIFIER ":" type ( "=" expression )? ";"
    type        -> "int" | "bool" | "str"
    assignment  -> IDENTIFIER "=" expression ";"
    log_stmt    -> "log" "(" expression ")" ";"
    if_stmt     -> "if" expression block ( "else" block )?
    block       -> "{" statement* "}"

    expression  -> term ( ( "+" | "-" ) term )*          (lowest precedence)
    term        -> unary ( ( "*" | "/" ) unary )*
    unary       -> "-" unary | primary
    primary     -> INT_LITERAL | STRING_LITERAL | BOOL_LITERAL
                  | IDENTIFIER | "(" expression ")"        (highest precedence)

Every rule is parsed by one method (`_parse_<rule>`). One token of lookahead is
enough to decide which alternative to take, i.e. the grammar is LL(1).
"""

from types import SimpleNamespace
from typing import List

from .ast_nodes import (
  Assignment, BinaryOp, Block, BoolLiteral, Identifier, IfStatement,
  IntLiteral, LogStatement, Node, Program, StringLiteral, UnaryOp, VarDecl,
)

TYPE_KEYWORDS = ("int", "bool", "str")

# Human-friendly names used when describing the token we actually found.
LITERAL_NAMES = {
  "INT_LITERAL": "integer literal",
  "STRING_LITERAL": "string literal",
  "BOOL_LITERAL": "boolean literal",
}


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class SyntaxAnalysisError(Exception):
  """Raised when the token stream does not match the grammar."""

  def __init__(self, message, line=None, column=None):
    self.message = message
    self.line = line
    self.column = column

    if line is None:
      full = f"Syntax Error: {message}"
    elif column is None:
      full = f"Syntax Error at line {line}: {message}"
    else:
      full = f"Syntax Error at line {line}, column {column}: {message}"
    super().__init__(full)


def describe(token):
  """Turn a token into readable text for error messages."""
  if token.type == "EOF":
    return "end of input"
  if token.type == "IDENTIFIER":
    return f"identifier '{token.value}'"
  if token.type == "KEYWORD":
    return f"keyword '{token.value}'"
  if token.type in LITERAL_NAMES:
    return f"{LITERAL_NAMES[token.type]} {token.value}"
  return f"'{token.value}'"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
  def __init__(self, tokens: List):
    self.tokens = tokens
    self.pos = 0
    self.eof = self._make_eof_token()

  # ----- public entry point ------------------------------------------------

  def parse(self) -> Program:
    """program -> statement* EOF"""
    start = self._peek()
    statements = []
    while not self._check("EOF"):
      statements.append(self._parse_statement())
    return self._at(Program(statements), start)

  # ----- token-stream helpers ---------------------------------------------

  def _make_eof_token(self):
    """The lexer emits no EOF token, so we invent one positioned after the last real token."""
    last = self.tokens[-1] if self.tokens else None
    return SimpleNamespace(type="EOF", value="", **self._end_position(last))

  @staticmethod
  def _end_position(token):
    """Position just past `token` (used for 'missing ;' and 'unexpected end of input')."""
    line = getattr(token, "line", None)
    column = getattr(token, "column", None)
    if column is not None:
      column += len(str(token.value))
    return {"line": line, "column": column}

  def _peek(self):
    """Current token without consuming it (EOF sentinel when we run out)."""
    return self.tokens[self.pos] if self.pos < len(self.tokens) else self.eof

  def _advance(self):
    """Consume and return the current token."""
    token = self._peek()
    if token.type != "EOF":
      self.pos += 1
    return token

  def _check(self, token_type, value=None):
    token = self._peek()
    return token.type == token_type and (value is None or token.value == value)

  def _match(self, token_type, value=None):
    """Consume the current token only if it matches; return whether it did."""
    if self._check(token_type, value):
      self._advance()
      return True
    return False

  def _expect(self, token_type, expected, context="", value=None,
              opened=None, report_after_previous=False):
    """
    Consume a token of the given type or raise a descriptive error.

    expected              text for the message, e.g. "';'"
    context               extra words, e.g. "after variable declaration"
    value                 optionally require a specific lexeme (for KEYWORDs)
    opened                the opening bracket token, so the message can point back to it
    report_after_previous point at the end of the previous token (used for a missing ';',
                          because the real mistake is on the previous line)
    """
    if self._check(token_type, value):
      return self._advance()

    found = self._peek()
    message = f"expected {expected}"
    if context:
      message += f" {context}"
    message += f", but found {describe(found)}"
    if opened is not None and getattr(opened, "line", None) is not None:
      message += f" (to match the '{opened.value}' opened at line {opened.line})"

    if report_after_previous and self.pos > 0:
      pos = self._end_position(self.tokens[self.pos - 1])
      raise SyntaxAnalysisError(message, pos["line"], pos["column"])
    raise self._error(message, found)

  @staticmethod
  def _error(message, token):
    return SyntaxAnalysisError(message, getattr(token, "line", None), getattr(token, "column", None))

  @staticmethod
  def _at(node: Node, token) -> Node:
    """Stamp a node with the source position of `token`."""
    node.line = getattr(token, "line", None)
    node.column = getattr(token, "column", None)
    return node

  # ----- statements --------------------------------------------------------

  def _parse_statement(self):
    """statement -> declaration | assignment | log_stmt | if_stmt"""
    token = self._peek()

    if token.type == "KEYWORD":
      if token.value == "dec":
        return self._parse_declaration()
      if token.value == "log":
        return self._parse_log()
      if token.value == "if":
        return self._parse_if()
      if token.value == "else":
        raise self._error("'else' without a matching 'if'", token)
      raise self._error(
        f"unexpected {describe(token)}; types may only appear in a declaration, after ':'", token)

    if token.type == "IDENTIFIER":
      return self._parse_assignment()

    if token.type == "RBRACE":
      raise self._error("unexpected '}' with no matching '{'", token)

    raise self._error(
      f"expected a statement ('dec', an assignment, 'log' or 'if'), but found {describe(token)}", token)

  def _parse_declaration(self):
    """declaration -> "dec" IDENTIFIER ":" type ( "=" expression )? ";" """
    dec = self._advance()
    name = self._expect("IDENTIFIER", "a variable name", "after 'dec'")
    self._expect("COLON", "':'", f"after '{name.value}' (declarations look like 'dec x : int;')")

    type_token = self._peek()
    if not (type_token.type == "KEYWORD" and type_token.value in TYPE_KEYWORDS):
      raise self._error(
        f"expected a type ('int', 'bool' or 'str') after ':', but found {describe(type_token)}", type_token)
    self._advance()

    initializer = None
    if self._match("ASSIGN"):
      initializer = self._parse_expression()

    self._expect("SEMICOLON", "';'", "after variable declaration", report_after_previous=True)
    return self._at(VarDecl(name.value, type_token.value, initializer), dec)

  def _parse_assignment(self):
    """assignment -> IDENTIFIER "=" expression ";" """
    name = self._advance()
    self._expect("ASSIGN", "'='", f"after '{name.value}' (assignments look like 'x = 1;')")
    value = self._parse_expression()
    self._expect("SEMICOLON", "';'", "after assignment", report_after_previous=True)
    return self._at(Assignment(name.value, value), name)

  def _parse_log(self):
    """log_stmt -> "log" "(" expression ")" ";" """
    log = self._advance()
    lparen = self._expect("LPAREN", "'('", "after 'log'")
    expression = self._parse_expression()
    self._expect("RPAREN", "')'", "after the value to log", opened=lparen)
    self._expect("SEMICOLON", "';'", "after log statement", report_after_previous=True)
    return self._at(LogStatement(expression), log)

  def _parse_if(self):
    """if_stmt -> "if" expression block ( "else" block )?"""
    if_token = self._advance()
    condition = self._parse_expression()
    then_block = self._parse_block("after the if condition")

    else_block = None
    if self._match("KEYWORD", "else"):
      else_block = self._parse_block("after 'else'")

    return self._at(IfStatement(condition, then_block, else_block), if_token)

  def _parse_block(self, context):
    """block -> "{" statement* "}" """
    lbrace = self._expect("LBRACE", "'{'", context)
    statements = []

    while not self._check("RBRACE"):
      if self._check("EOF"):
        where = f" opened at line {lbrace.line}" if getattr(lbrace, "line", None) else ""
        raise self._error(f"expected '}}' to close the block{where}, but reached end of input", self._peek())
      statements.append(self._parse_statement())

    self._advance()  # consume '}'
    return self._at(Block(statements), lbrace)

  # ----- expressions (one method per precedence level) ---------------------

  def _parse_expression(self):
    """expression -> term ( ("+" | "-") term )*   -- left associative"""
    left = self._parse_term()
    while self._peek().type in ("PLUS", "SUBTRACT"):
      op = self._advance()
      right = self._parse_term()
      left = self._at(BinaryOp(op.value, left, right), op)
    return left

  def _parse_term(self):
    """term -> unary ( ("*" | "/") unary )*   -- left associative"""
    left = self._parse_unary()
    while self._peek().type in ("MULTIPLY", "DIVIDE"):
      op = self._advance()
      right = self._parse_unary()
      left = self._at(BinaryOp(op.value, left, right), op)
    return left

  def _parse_unary(self):
    """unary -> "-" unary | primary"""
    if self._check("SUBTRACT"):
      op = self._advance()
      return self._at(UnaryOp(op.value, self._parse_unary()), op)
    return self._parse_primary()

  def _parse_primary(self):
    """primary -> INT_LITERAL | STRING_LITERAL | BOOL_LITERAL | IDENTIFIER | "(" expression ")" """
    token = self._peek()

    if token.type == "INT_LITERAL":
      self._advance()
      return self._at(IntLiteral(int(token.value)), token)

    if token.type == "STRING_LITERAL":
      self._advance()
      return self._at(StringLiteral(token.value[1:-1]), token)  # strip the quotes

    if token.type == "BOOL_LITERAL":
      self._advance()
      return self._at(BoolLiteral(token.value == "True"), token)

    if token.type == "IDENTIFIER":
      self._advance()
      # WORKAROUND: the current lexer tries IDENTIFIER before BOOL_LITERAL, so True/False
      # arrive as IDENTIFIERs. This branch becomes dead code once the lexer is fixed.
      if token.value in ("True", "False"):
        return self._at(BoolLiteral(token.value == "True"), token)
      return self._at(Identifier(token.value), token)

    if token.type == "LPAREN":
      lparen = self._advance()
      inner = self._parse_expression()
      self._expect("RPAREN", "')'", "to close the parenthesized expression", opened=lparen)
      return inner  # grouping is already encoded by the tree shape

    raise self._error(f"expected an expression, but found {describe(token)}", token)


# ---------------------------------------------------------------------------
# Convenience function (mirrors `lex(code)` from Phase 1)
# ---------------------------------------------------------------------------

def parse(tokens: List) -> Program:
  """Parse a token list into an AST. Raises SyntaxAnalysisError on invalid input."""
  return Parser(tokens).parse()