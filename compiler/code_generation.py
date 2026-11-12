# Phase 4: Code Generation and Execution

# generates intermediate code (three-address code)
def generate_tac(ast):
  instructions = []
  # todo: traverse ast and generate instructions
  return instructions


# optimizes instructions (constant folding, dead code removal)
def optimize(instructions):
  # todo: optimize pass
  return instructions


# virtual machine to execute instructions
def execute(instructions):
  memory = {}
  # todo: run instructions using memory
  pass


def generate_code(ast, should_optimize=True):
  instructions = generate_tac(ast)
  if should_optimize:
    instructions = optimize(instructions)

  return execute(instructions)
