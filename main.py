from compiler.lexical_analysis import lex
from compiler.syntax_analysis import parse, SyntaxAnalysisError
from compiler.semantic_analysis import analyze, SemanticAnalysisError
from compiler.code_generation import generate_code
from compiler.ast_nodes import dump

sample_source_codes = [

  # Test 1
  """
  dec x : int;
  dec y : int;
  x = 1;
  y = 2;
  log(x + y);
  """,

  # Test 2
  """
  dec name : str = "John";
  dec age : int = 20;
  log("My name is " + name + "and I am " + age + "years old.");
  """,

  # Test 3
  """
  dec tired : bool = True;
  if tired {
    log("Deal with it");
  } else {
    log("Nice");
  }
  """

]

def main():
  for i, code in enumerate(sample_source_codes, 1):
    print("=" * 60)
    print(f"RUNNING TEST {i}")
    print("=" * 60)

    # Phase 1: Lexical Analysis
    tokens = lex(code)
    print("Tokens:", tokens)

    # Phase 2: Syntax Analysis
    try:
      ast = parse(tokens)
      print("\nAST:\n" + dump(ast))
    except SyntaxAnalysisError as e:
      print(f"\nSyntax Error: {e}\n")
      continue

    # Phase 3: Semantic Analysis
    try:
      analyzed_ast = analyze(ast)
      print("\nSemantic analysis passed.")
    except SemanticAnalysisError as e:
      print()
      for error in e.errors:
        print(error)
      continue

    # Phase 4: Code Generation and Execution
    print("\nOutput:")
    generate_code(analyzed_ast)
    print()

if __name__ == "__main__":
  main()
