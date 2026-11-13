import unittest

from compiler.lexical_analysis import lex
from compiler.syntax_analysis import parse
from compiler.semantic_analysis import analyze, SemanticAnalysisError


def check(source):
  """Run lexer -> parser -> semantic analysis. Returns the list of error messages (empty = OK)."""
  try:
    analyze(parse(lex(source)))
  except SemanticAnalysisError as e:
    return [err.message for err in e.errors]
  return []


class ValidPrograms(unittest.TestCase):
  def test_sample_program_from_spec(self):
    src = """
      dec x : int;
      dec y : int;
      dec z : bool;
      x = 1;
      y = 2;
      z = True;
      if z { log(x + y); } else { log(x * y); }
    """
    self.assertEqual(check(src), [])

  def test_declaration_with_initializer(self):
    self.assertEqual(check('dec s : str = "hi"; dec n : int = 2 * 3; log(s); log(n);'), [])

  def test_shadowing_in_inner_block_is_allowed(self):
    src = "dec x : int = 1; if True { dec x : bool = False; log(x); }"
    self.assertEqual(check(src), [])

  def test_assigned_in_both_branches_counts_as_initialized(self):
    src = "dec x : int; if True { x = 1; } else { x = 2; } log(x);"
    self.assertEqual(check(src), [])

  def test_unary_minus_and_parens(self):
    self.assertEqual(check("dec x : int = -(1 + 2) * 3; log(x);"), [])


class DeclarationErrors(unittest.TestCase):
  def test_duplicate_in_same_scope(self):
    errs = check("dec x : int; dec x : bool;")
    self.assertEqual(len(errs), 1)
    self.assertIn("already declared", errs[0])

  def test_undeclared_read(self):
    errs = check("log(y);")
    self.assertEqual(errs, ["use of undeclared variable 'y'"])

  def test_undeclared_assignment(self):
    errs = check("y = 1;")
    self.assertEqual(errs, ["assignment to undeclared variable 'y'"])

  def test_inner_variable_not_visible_outside_block(self):
    errs = check("if True { dec a : int = 1; } log(a);")
    self.assertEqual(errs, ["use of undeclared variable 'a'"])

  def test_initializer_cannot_use_the_variable_being_declared(self):
    errs = check("dec x : int = x;")
    self.assertEqual(errs, ["use of undeclared variable 'x'"])


class InitializationErrors(unittest.TestCase):
  def test_read_before_assignment(self):
    errs = check("dec x : int; log(x);")
    self.assertEqual(len(errs), 1)
    self.assertIn("before it is assigned", errs[0])

  def test_assigned_in_only_one_branch(self):
    errs = check("dec x : int; if True { x = 1; } log(x);")
    self.assertEqual(len(errs), 1)
    self.assertIn("before it is assigned", errs[0])

  def test_assigned_in_then_but_else_missing_a_value(self):
    errs = check("dec x : int; if True { x = 1; } else { log(1); } log(x);")
    self.assertEqual(len(errs), 1)


class TypeErrors(unittest.TestCase):
  def test_assign_wrong_type(self):
    errs = check('dec x : int; x = "hello";')
    self.assertEqual(len(errs), 1)
    self.assertIn("cannot assign a value of type str", errs[0])

  def test_initializer_wrong_type(self):
    errs = check("dec b : bool = 1;")
    self.assertEqual(len(errs), 1)
    self.assertIn("cannot initialize 'b'", errs[0])

  def test_arithmetic_on_bool(self):
    errs = check("dec b : bool = True; log(b + 1);")
    self.assertEqual(len(errs), 1)
    self.assertIn("needs int operands", errs[0])

  def test_string_arithmetic(self):
    errs = check('log("a" + "b");')
    self.assertEqual(len(errs), 1)

  def test_unary_minus_on_bool(self):
    errs = check("log(-True);")
    self.assertEqual(len(errs), 1)

  def test_if_condition_must_be_bool(self):
    errs = check("dec x : int = 1; if x { log(x); }")
    self.assertEqual(errs, ["'if' condition must be bool, but found int"])

  def test_division_by_literal_zero(self):
    errs = check("log(4 / 0);")
    self.assertEqual(errs, ["division by zero"])


class ErrorReporting(unittest.TestCase):
  def test_all_errors_are_reported_not_just_the_first(self):
    errs = check("dec x : int; log(y); x = True; dec x : int;")
    self.assertEqual(len(errs), 3)

  def test_one_mistake_does_not_cascade(self):
    # `ghost` is undeclared; the surrounding `+` and the assignment must not add more errors.
    errs = check("dec x : int; x = ghost + 1;")
    self.assertEqual(errs, ["use of undeclared variable 'ghost'"])


class Annotations(unittest.TestCase):
  def test_types_and_unique_names_are_attached_for_codegen(self):
    program = analyze(parse(lex("dec x : int = 1; if True { dec x : int = 2; log(x); }")))
    outer_decl = program.statements[0]
    inner_decl = program.statements[1].then_block.statements[0]
    inner_use = program.statements[1].then_block.statements[1].expression
    self.assertEqual(outer_decl.symbol.unique_name, "x")
    self.assertEqual(inner_decl.symbol.unique_name, "x_1")
    self.assertIs(inner_use.symbol, inner_decl.symbol)
    self.assertEqual(inner_use.inferred_type, "int")


if __name__ == "__main__":
  unittest.main()
