# Compiler

Our final group project for CSAL102: Automata and Formal Langauges.

## Programming Language

[Draft 1] is a simple, statically-typed, and imperative toy language we designed to demonstrate the core phases of a compiler from source code to execution.

```
// Declaration
dec x : int;
dec y : int;
dec z : bool;

// Assignment
x = 1;
y = 2;
z = True;

// Printing
if z {
  log(x + y);
} else {
  log(x * y);
}
```

## Compiler Phases

Our compiler development is split into steps handled across the team:

### Phase 1: Lexical Analysis

Breaks down the raw source code into tokens using regex.

### Phase 2: Syntax Analysis

Organizes tokens into an Abstract Syntax Tree (AST) following our custom grammar rules.

### Phase 3: Semantic Analysis

Checks for type mismatches, undeclared variables, and duplicate declarations using a symbol table.

### Phase 4: Code Generation and Execution

Generates pseudo-instructions and runs them.

## Team

| Name            | Phase            |
| --------------- | ---------------- |
| Neil Tagle      | Lexical Analysis |
| Vincent Aguirre | ...              |
| Kyla Dequito    | ...              |
| Ace Gamitin     | ...              |
