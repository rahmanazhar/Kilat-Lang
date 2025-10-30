#!/usr/bin/env python3
"""
Kilat-Lang Compiler/Interpreter
Main entry point for compiling and executing Kilat-Lang programs
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
        print("Usage: python kilat.py <source_file.klt> [--compile-only] [-o output.py]")
        print("Options:")
        print("  --compile-only    Compile to Python without executing")
        print("  -o output.py      Specify output file (use with --compile-only)")
        sys.exit(1)
    
    source_file = sys.argv[1]
    
    if not os.path.exists(source_file):
        print(f"Error: File '{source_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    compiler = KilatCompiler(source_file=source_file)
    
    # Check for flags
    if '--compile-only' in sys.argv:
        # Compile only mode
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
        # Compile and run mode (default)
        compiler.compile_and_run()


if __name__ == '__main__':
    main()
