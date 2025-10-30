#!/bin/bash

# Test script for Kilat-Lang
# This script runs all example programs to verify the compiler works correctly

echo "=========================================="
echo "  Testing Kilat-Lang Compiler"
echo "=========================================="
echo ""

# Array of test files
tests=(
    "examples/hello_world.klt"
    "examples/for_loop.klt"
    "examples/conditionals.klt"
    "examples/functions.klt"
    "examples/classes.klt"
    "examples/calculator.klt"
)

# Counter for passed tests
passed=0
total=${#tests[@]}

# Run each test
for test_file in "${tests[@]}"; do
    echo "Testing: $test_file"
    echo "----------------------------------------"
    
    if python kilat.py "$test_file"; then
        echo "✓ PASSED"
        ((passed++))
    else
        echo "✗ FAILED"
    fi
    
    echo ""
    echo ""
done

# Summary
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Passed: $passed / $total"

if [ $passed -eq $total ]; then
    echo "All tests passed! ✓"
    exit 0
else
    echo "Some tests failed."
    exit 1
fi
