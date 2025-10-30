#!/usr/bin/env python3
"""
Kilat-Lang Compiler/Interpreter
Main entry point for compiling and executing Kilat-Lang programs

Modes:
1. Native mode (--native): Uses independent interpreter (no Python dependency)
2. Transpile mode (default): Transpiles to Python and executes
"""

import sys
import os
from kilat_translator import KilatTranslator


class KilatCompiler:
    """Main compiler class for Kilat-Lang"""
    
    def __init__(self, source_file=None, source_code=None):
        self.source_file = source_file
        self.source_code = source_code
        
        if source_file and not source_code:
            with open(source_file, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
    
    def compile(self):
        """
        Compile Kilat-Lang source to Python
        """
        translator = KilatTranslator(self.source_code)
        python_code = translator.translate()
        return python_code
    
    def compile_and_save(self, output_file=None):
        """
        Compile and save to a Python file
        """
        python_code = self.compile()
        
        if not output_file and self.source_file:
            # Generate output filename from source filename
            output_file = self.source_file.rsplit('.', 1)[0] + '.py'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        return output_file
    
    def compile_and_run(self):
        """
        Compile and execute the Kilat-Lang program
        """
        python_code = self.compile()
        
        # Execute the Python code
        try:
            # Create a clean namespace for execution
            exec_globals = {'__name__': '__main__', '__file__': self.source_file or '<kilat>'}
            exec(python_code, exec_globals)
        except Exception as e:
            print(f"Error executing Kilat-Lang program: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """
    Main entry point for the Kilat compiler
    """
    if len(sys.argv) < 2:
        print("Usage: python kilat.py <source_file.klt> [options]")
        print("\nOptions:")
        print("  --native          Use native interpreter (independent from Python)")
        print("  --compile-only    Compile to Python without executing")
        print("  -o output.py      Specify output file (use with --compile-only)")
        print("\nExamples:")
        print("  python kilat.py program.klt              # Transpile and run")
        print("  python kilat.py program.klt --native     # Run with native interpreter")
        print("  python kilat.py program.klt --compile-only  # Just compile to Python")
        sys.exit(1)
    
    source_file = sys.argv[1]
    
    if not os.path.exists(source_file):
        print(f"Error: File '{source_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Check for native mode
    if '--native' in sys.argv:
        # Use native interpreter
        from kilat_interpreter import run_kilat
        
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        try:
            run_kilat(source_code)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    elif '--compile-only' in sys.argv:
        # Compile only mode
        compiler = KilatCompiler(source_file=source_file)
        output_file = None
        if '-o' in sys.argv:
            try:
                output_index = sys.argv.index('-o')
                output_file = sys.argv[output_index + 1]
            except (IndexError, ValueError):
                print("Error: -o flag requires an output filename", file=sys.stderr)
                sys.exit(1)
        
        output_file = compiler.compile_and_save(output_file)
        print(f"Compiled successfully to: {output_file}")
    
    else:
        # Compile and run mode (default - transpile to Python)
        compiler = KilatCompiler(source_file=source_file)
        compiler.compile_and_run()


if __name__ == '__main__':
    main()
