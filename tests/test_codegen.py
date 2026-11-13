import unittest

from compiler.lexical_analysis import lex
from compiler.syntax_analysis import parse
from compiler.semantic_analysis import analyze
from compiler.code_generation import generate_code, generate_tac, optimize


def run(source, should_optimize=True):
  """Helper to run the full pipeline: lex -> parse -> analyze -> codegen."""
  ast = analyze(parse(lex(source)))
  return generate_code(ast, should_optimize=should_optimize)


class CodeGenerationTests(unittest.TestCase):
  def test_simple_arithmetic(self):
    src = """
      dec x : int = 1;
      dec y : int = 2;
      log(x + y);
    """
    self.assertEqual(run(src), ["3"])

  def test_operator_precedence(self):
    src = """
      dec x : int = 2 + 3 * 4;
      log(x);
    """
    self.assertEqual(run(src), ["14"])

  def test_if_else_branching_true(self):
    src = """
      dec tired : bool = True;
      if tired {
        log("Deal with it");
      } else {
        log("Nice");
      }
    """
    self.assertEqual(run(src), ["Deal with it"])

  def test_if_else_branching_false(self):
    src = """
      dec tired : bool = False;
      dec x : int = 0;
      if tired {
        x = 1;
      } else {
        x = 2;
      }
      log(x);
    """
    self.assertEqual(run(src), ["2"])

  def test_variable_shadowing(self):
    # ace's unique_name ensures inner x doesn't overwrite outer x
    src = """
      dec x : int = 10;
      if True {
        dec x : int = 99;
        log(x);
      }
      log(x);
    """
    self.assertEqual(run(src), ["99", "10"])

  def test_optimization_constant_folding_and_dce(self):
    src = """
      dec a : int = 10;
      dec b : int = 20;
      dec c : int = a + 0;
      dec unused : int = b * 0;
      c = c + (5 * 2);
      log(c);
    """
    # both unoptimized and optimized should give identical output
    self.assertEqual(run(src, should_optimize=False), ["20"])
    self.assertEqual(run(src, should_optimize=True), ["20"])


if __name__ == "__main__":
  unittest.main()
