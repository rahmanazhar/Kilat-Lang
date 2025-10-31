# Kilat-Lang Test Suite

## Running Tests

### Native Interpreter Tests
```bash
python test_native.py
```

This comprehensive test suite verifies that the **native interpreter mode** works independently without Python dependencies.

## Test Coverage

The test suite includes **25 comprehensive tests** covering:

### Basic Operations (Tests 1-3)
- ✅ Arithmetic operations (+, -, *, /, %, **)
- ✅ Variable assignments
- ✅ Basic if statements

### Control Flow (Tests 4-6)
- ✅ If-elif-else chains
- ✅ For loops with ranges
- ✅ While loops

### Functions (Tests 7-9)
- ✅ Function definitions and calls
- ✅ Functions with default parameters
- ✅ Nested function calls
- ✅ Recursion (factorial)

### Data Structures (Tests 10-11, 19)
- ✅ Lists (creation, indexing, length)
- ✅ List iteration
- ✅ Dictionaries

### Operators (Tests 12-13)
- ✅ Comparison operators (>, <, ==, !=, >=, <=)
- ✅ Logical operators (dan, atau_logik, bukan)

### Loop Control (Tests 14-16)
- ✅ Break statements
- ✅ Continue statements
- ✅ Nested loops

### Object-Oriented (Test 17)
- ✅ Class definitions
- ✅ Instance creation
- ✅ Method calls
- ✅ Attribute assignment

### Advanced Features (Tests 18-25)
- ✅ Recursive functions
- ✅ String concatenation
- ✅ Multiple assignments
- ✅ Negative numbers
- ✅ Complex expressions
- ✅ Boolean variables
- ✅ None values

## Test Results

When all tests pass, you'll see:
```
╔═══════════════════════════════════════════════════════╗
║   🎉 ALL TESTS PASSED! 🎉                            ║
║   Kilat-Lang Native Interpreter is working!          ║
╚═══════════════════════════════════════════════════════╝
```

## Test Structure

Each test:
1. Creates a temporary `.klt` file with test code
2. Runs it with `python kilat.py <file> --native`
3. Compares output with expected results
4. Reports pass/fail status
5. Cleans up temporary files

## Adding New Tests

To add a new test, edit `test_native.py` and add to the `create_tests()` function:

```python
tests.append(TestCase(
    "Test Name",
    """kilat code here
cetak("output")""",
    """expected output"""
))
```

## Continuous Testing

Run tests after any changes to:
- `kilat_lexer2.py` - Lexer
- `kilat_parser.py` - Parser
- `kilat_interpreter.py` - Interpreter
- `kilat_ast.py` - AST definitions

## Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| Arithmetic | 3 | ✅ |
| Control Flow | 3 | ✅ |
| Functions | 4 | ✅ |
| Data Structures | 3 | ✅ |
| Operators | 2 | ✅ |
| Loop Control | 3 | ✅ |
| OOP | 1 | ✅ |
| Advanced | 6 | ✅ |
| **Total** | **25** | **✅** |

## Performance

Tests typically complete in **2-3 seconds** for all 25 tests.

## Troubleshooting

If tests fail:
1. Check the error message for line/column numbers
2. Look at stderr output for parser/interpreter errors
3. Run the failing test manually: `python kilat.py test_temp_*.klt --native`
4. Compare expected vs actual output

## Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Test Kilat-Lang Native Interpreter
  run: python test_native.py
```

## License

Same as Kilat-Lang project.
