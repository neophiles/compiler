import re

TOKEN_SPECIFICATIONS = [
  # keywords and identifiers
  ("KEYWORD", r"\b(dec|int|bool|str|log|if|else)\b"),
  ("IDENTIFIER", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),

  # literals
  ("STRING_LITERAL", r'"[^"]*"'),
  ("BOOL_LITERAL", r"\b(True|False)\b"),
  ("INT_LITERAL", r"\b\d+\b"),
  
  # operators
  ("ASSIGN", r"="),
  ("PLUS", r"\+"),
  ("SUBTRACT", r"\-"),
  ("MULTIPLY", r"\*"),
  ("DIVIDE", r"/"),
  
  # punctuations and delimiters
  ("COLON", r":"),
  ("SEMICOLON", r";"),
  ("LPAREN", r"\("),
  ("RPAREN", r"\)"),
  ("LBRACE", r"\{"),
  ("RBRACE", r"\}"),
  
  # whitespace (ignored :D)
  ("WHITESPACE", r"\s+"),
]


class Token:
  def __init__(self, _type, value):
    self.type = _type
    self.value = value

  def __repr__(self):
    return f"Token({self.type}, '{self.value}')"


def lex(code):
  tokens = []
  regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATIONS)

  for match in re.finditer(regex, code):
    type = match.lastgroup
    val = match.group(type)

    if type == "WHITESPACE":
      continue

    tokens.append(Token(type, val))

  return tokens
