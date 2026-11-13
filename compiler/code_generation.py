# Phase 4: Code Generation and Execution

import sys
from pathlib import Path

# allow running directly or as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compiler.ast_nodes import (
  Assignment, BinaryOp, Block, BoolLiteral, Identifier, IfStatement,
  IntLiteral, LogStatement, Program, StringLiteral, UnaryOp, VarDecl,
)


def var_name(node):
  # ace annotated symbols with unique_name for safe variable shadowing
  if hasattr(node, "symbol") and node.symbol is not None:
    return node.symbol.unique_name
  return getattr(node, "name", str(node))


def is_num(val):
  if val is None:
    return False
  if isinstance(val, int):
    return True
  if isinstance(val, str) and (val.isdigit() or (val.startswith("-") and len(val) > 1 and val[1:].isdigit())):
    return True
  return False


# generates intermediate code (three-address code)
def generate_tac(ast):
  instructions = []
  temp_count = 0
  label_count = 0

  def new_temp():
    nonlocal temp_count
    temp_count += 1
    return f"t{temp_count}"

  def new_label():
    nonlocal label_count
    label_count += 1
    return f"L{label_count}"

  def walk(node):
    if isinstance(node, IntLiteral):
      return str(node.value)
    elif isinstance(node, StringLiteral):
      return f'"{node.value}"'
    elif isinstance(node, BoolLiteral):
      return str(node.value)
    elif isinstance(node, Identifier):
      return var_name(node)
    elif isinstance(node, UnaryOp):
      val = walk(node.operand)
      t = new_temp()
      instructions.append(("SUB", "0", val, t))
      return t
    elif isinstance(node, BinaryOp):
      l = walk(node.left)
      r = walk(node.right)
      t = new_temp()
      op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
      instructions.append((op_map[node.op], l, r, t))
      return t
    elif isinstance(node, VarDecl):
      if node.initializer is not None:
        val = walk(node.initializer)
        instructions.append(("MOV", val, None, var_name(node)))
    elif isinstance(node, Assignment):
      val = walk(node.value)
      instructions.append(("MOV", val, None, var_name(node)))
    elif isinstance(node, LogStatement):
      val = walk(node.expression)
      instructions.append(("PRINT", val, None, None))
    elif isinstance(node, IfStatement):
      cond = walk(node.condition)
      else_lbl = new_label()
      end_lbl = new_label()
      instructions.append(("JUMP_IF_FALSE", cond, None, else_lbl))
      walk(node.then_block)
      instructions.append(("JUMP", end_lbl, None, None))
      instructions.append(("LABEL", else_lbl, None, None))
      if node.else_block is not None:
        walk(node.else_block)
      instructions.append(("LABEL", end_lbl, None, None))
    elif isinstance(node, (Block, Program)):
      for stmt in node.statements:
        walk(stmt)

  walk(ast)
  return instructions


# optimizes instructions (constant folding, dead code removal)
def optimize(instructions):
  current = list(instructions)

  for _ in range(10):
    changed = False
    new_instrs = []
    constants = {}

    for instr in current:
      op, a1, a2, res = instr

      # reset constants at control flow boundaries
      if op in ("LABEL", "JUMP", "JUMP_IF_FALSE"):
        constants.clear()
        new_instrs.append(instr)
        continue

      if op == "PRINT":
        new_instrs.append(instr)
        continue

      # constant propagation
      if a1 in constants:
        a1 = constants[a1]
        changed = True
      if a2 in constants:
        a2 = constants[a2]
        changed = True

      # constant folding
      if op in ("ADD", "SUB", "MUL", "DIV") and is_num(a1) and is_num(a2):
        v1, v2 = int(a1), int(a2)
        val = None
        if op == "ADD": val = v1 + v2
        elif op == "SUB": val = v1 - v2
        elif op == "MUL": val = v1 * v2
        elif op == "DIV" and v2 != 0: val = v1 // v2

        if val is not None:
          instr = ("MOV", str(val), None, res)
          a1 = str(val)
          changed = True

      # algebraic simplification
      elif op == "ADD":
        if is_num(a2) and int(a2) == 0: instr = ("MOV", a1, None, res); changed = True
        elif is_num(a1) and int(a1) == 0: instr = ("MOV", a2, None, res); changed = True
      elif op == "SUB" and is_num(a2) and int(a2) == 0:
        instr = ("MOV", a1, None, res); changed = True
      elif op == "MUL":
        if (is_num(a2) and int(a2) == 0) or (is_num(a1) and int(a1) == 0):
          instr = ("MOV", "0", None, res); changed = True
        elif is_num(a2) and int(a2) == 1: instr = ("MOV", a1, None, res); changed = True
        elif is_num(a1) and int(a1) == 1: instr = ("MOV", a2, None, res); changed = True

      new_instrs.append(instr)

      if instr[0] == "MOV" and is_num(instr[1]) and instr[3]:
        constants[instr[3]] = instr[1]
      elif instr[3]:
        constants.pop(instr[3], None)

    # dead code elimination
    live = set()
    dce_instrs = []
    for instr in reversed(new_instrs):
      op, a1, a2, res = instr
      if op in ("PRINT", "LABEL", "JUMP", "JUMP_IF_FALSE"):
        dce_instrs.append(instr)
        if a1 and not is_num(a1) and not a1.startswith('"'): live.add(a1)
        if a2 and not is_num(a2) and not a2.startswith('"'): live.add(a2)
      elif res:
        if res in live:
          dce_instrs.append(instr)
          live.remove(res)
          if a1 and not is_num(a1) and not a1.startswith('"'): live.add(a1)
          if a2 and not is_num(a2) and not a2.startswith('"'): live.add(a2)
        else:
          changed = True
      else:
        dce_instrs.append(instr)

    dce_instrs.reverse()
    current = dce_instrs
    if not changed:
      break

  return current


# virtual machine to execute instructions
def execute(instructions):
  memory = {}
  output = []

  labels = {}
  for idx, instr in enumerate(instructions):
    if instr[0] == "LABEL":
      labels[instr[1]] = idx

  def get_val(op):
    if op is None:
      return None
    if isinstance(op, int):
      return op
    if isinstance(op, str):
      if op == "True": return True
      if op == "False": return False
      if is_num(op): return int(op)
      if op.startswith('"') and op.endswith('"'): return op[1:-1]
      if op in memory: return memory[op]
      raise RuntimeError(f"variable '{op}' used before initialization")
    return op

  pc = 0
  while pc < len(instructions):
    op, a1, a2, res = instructions[pc]

    if op == "MOV":
      memory[res] = get_val(a1)
    elif op == "ADD":
      v1, v2 = get_val(a1), get_val(a2)
      if isinstance(v1, str) or isinstance(v2, str):
        memory[res] = str(v1) + str(v2)
      else:
        memory[res] = v1 + v2
    elif op == "SUB":
      memory[res] = get_val(a1) - get_val(a2)
    elif op == "MUL":
      memory[res] = get_val(a1) * get_val(a2)
    elif op == "DIV":
      v2 = get_val(a2)
      if v2 == 0: raise ZeroDivisionError("division by zero")
      memory[res] = get_val(a1) // v2
    elif op == "PRINT":
      val = str(get_val(a1))
      output.append(val)
      print(val)
    elif op == "LABEL":
      pass
    elif op == "JUMP":
      pc = labels[a1]
      continue
    elif op == "JUMP_IF_FALSE":
      if not bool(get_val(a1)):
        pc = labels[res]
        continue

    pc += 1

  return output


def generate_code(ast, should_optimize=True):
  instructions = generate_tac(ast)
  if should_optimize:
    instructions = optimize(instructions)

  return execute(instructions)


if __name__ == "__main__":
  from compiler.lexical_analysis import lex
  from compiler.syntax_analysis import parse
  from compiler.semantic_analysis import analyze

  code = """
  dec x : int = 10;
  dec y : int = 20;
  dec unused : int = 99;
  log(x + y);
  """
  ast = analyze(parse(lex(code)))
  print("Output:")
  generate_code(ast)

