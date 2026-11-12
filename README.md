# Compiler

Our final group project for CSAL102: Automata and Formal Langauges.

## Programming Language

[Draft 1] is a simple, statically-typed, imperative, and semicolon-terminated toy language we designed to demonstrate the core phases of a compiler from source code to execution.

This draws inspiration from Python for general simplicity and Java for brace scoping, static typing and semicolon strictness.

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

**Current limitations**

- No decimal or floating-point support, only integers
- No escape sequence and internal quotation marks support for strings
- No comment support

### Phase 2: Syntax Analysis

Organizes tokens into an Abstract Syntax Tree (AST) using a Recursive Descent Parser following our custom LL(1) grammar rules.

**Current limitations**
- No loop control structures (e.g., `while`, `for`), only `if`/`else` branching
- No relational (`==`, `<`, `>`) or logical (`&&`, `||`) operators; conditions rely solely on boolean variables
- No custom function declarations or complex data structures (arrays, objects)

### Phase 3: Semantic Analysis

Checks for type mismatches, undeclared variables, and duplicate declarations using a symbol table.

### Phase 4: Code Generation and Execution

Generates pseudo-instructions and runs them.

## Getting Started

### Prerequisites

- [Python](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (optional)

### Run locally

```bash
# Clone the repository
git clone https://github.com/neophiles/compiler.git

# Run main
uv run main.py # OR python main.py
```

## Team

| Name            | Phase                         |
| --------------- | ----------------------------- |
| Neil Tagle      | Lexical Analysis              |
| Kyla Dequito    | Syntax Analysis               |
| Ace Gamitin     | Semantic Analysis             |
| Vincent Aguirre | Code Generation and Execution |
