from compiler.lexical_analysis import lex

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
  # testing lexical analysis
  for i in range(len(sample_source_codes)):
    print(f"Test {i+1}:", lex(sample_source_codes[i]), end="\n\n")

  # Phase 1: Lexical Analysis (uncomment this if next phase is done)
  # tokens = lex(sample_source_codes[0])
  # print("Tokens:", tokens)

  # Phase 2: Syntax Analysis
  ...

  # Phase 3: Semantic Analysis
  ...

  # Phase 4: Code Generation and Execution
  ...

if __name__ == "__main__":
  main()
