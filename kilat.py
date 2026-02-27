#!/usr/bin/env python3
"""
Kilat-Lang  ⚡
Bahasa pengaturcaraan sintaks Melayu berdasarkan Python.

Mod:
  1. Native (--native)     — interpreter tersendiri, tanpa kebergantungan Python
  2. Transpile (lalai)     — transpil ke Python dan jalankan
  3. Compile (--compile-only) — hanya transpil, simpan fail .py
  4. REPL   (--repl)       — shell interaktif
  5. Bytecode (--bytecode) — kompil ke kod bait dan jalankan pada VM
  6. Compile BC (--compile-bc) — kompil ke fail .klc sahaja
  7. Run KLC (--run-klc)   — jalankan fail .klc yang telah dikompil
"""

import sys
import os

__version__ = '1.0.0'


# ------------------------------------------------------------------ #
#  Transpile-mode compiler                                             #
# ------------------------------------------------------------------ #

class KilatCompiler:
    """Transpile Kilat-Lang source to Python and optionally execute it."""

    def __init__(self, source_file: str = None, source_code: str = None):
        self.source_file = source_file
        self.source_code = source_code

        if source_file and source_code is None:
            with open(source_file, 'r', encoding='utf-8') as f:
                self.source_code = f.read()

    def compile(self) -> str:
        from kilat_translator import KilatTranslator
        translator = KilatTranslator(self.source_code)
        return translator.translate()

    def compile_and_save(self, output_file: str = None) -> str:
        python_code = self.compile()

        if output_file is None and self.source_file:
            output_file = os.path.splitext(self.source_file)[0] + '.py'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(python_code)
        return output_file

    def compile_and_run(self):
        python_code = self.compile()
        exec_globals = {
            '__name__': '__main__',
            '__file__': self.source_file or '<kilat>',
        }
        try:
            exec(compile(python_code, self.source_file or '<kilat>', 'exec'), exec_globals)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Ralat: {e}", file=sys.stderr)
            sys.exit(1)


# ------------------------------------------------------------------ #
#  CLI entry point                                                     #
# ------------------------------------------------------------------ #

_USAGE = """\
Penggunaan: kilat <fail.klt> [pilihan]
       kilat --repl

Pilihan:
  --native          Jalankan dengan interpreter asli (tanpa Python)
  --bytecode        Kompil ke kod bait dan jalankan pada VM
  --compile-bc      Kompil ke fail .klc sahaja
  --run-klc         Jalankan fail .klc yang telah dikompil
  --repl            Buka shell interaktif (REPL)
  --compile-only    Transpil ke Python tanpa menjalankan
  -o <fail>         Fail output untuk --compile-only / --compile-bc
  --version         Papar versi
  --help, -h        Papar bantuan ini

Contoh:
  kilat program.klt              # Transpil dan jalankan
  kilat program.klt --native     # Jalankan dengan interpreter asli
  kilat program.klt --bytecode   # Kompil + jalankan via VM
  kilat program.klt --compile-bc # Kompil ke program.klc
  kilat program.klc --run-klc    # Jalankan fail .klc
  kilat program.klt --compile-only -o output.py
  kilat --repl                   # Shell interaktif
"""


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(_USAGE)
        sys.exit(0 if args else 1)

    if '--version' in args:
        print(f"Kilat-Lang {__version__}")
        sys.exit(0)

    # REPL mode
    if '--repl' in args or args[0] == '--repl':
        from kilat_repl import KilatREPL
        KilatREPL().run()
        return

    source_file = args[0]
    if not source_file.endswith('.klt') and not os.path.exists(source_file):
        print(f"Ralat: Fail '{source_file}' tidak ditemui", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(source_file):
        print(f"Ralat: Fail '{source_file}' tidak ditemui", file=sys.stderr)
        sys.exit(1)

    # Native interpreter mode
    if '--native' in args:
        from kilat_interpreter import run_kilat
        with open(source_file, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            run_kilat(source, filename=source_file)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Ralat: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Bytecode VM mode: compile and run via VM
    if '--bytecode' in args:
        from kilat_vm import run_bytecode
        with open(source_file, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            run_bytecode(source, filename=source_file)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Ralat: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Compile to .klc bytecode file
    if '--compile-bc' in args:
        from kilat_compiler import compile_kilat
        from kilat_bytecode import serialize_code
        with open(source_file, 'r', encoding='utf-8') as f:
            source = f.read()
        code = compile_kilat(source, filename=source_file)
        output_file = None
        if '-o' in args:
            try:
                output_file = args[args.index('-o') + 1]
            except IndexError:
                print("Ralat: -o memerlukan nama fail output", file=sys.stderr)
                sys.exit(1)
        if output_file is None:
            output_file = os.path.splitext(source_file)[0] + '.klc'
        with open(output_file, 'wb') as f:
            f.write(serialize_code(code))
        print(f"Berjaya dikompil ke kod bait: {output_file}")
        return

    # Run pre-compiled .klc file
    if '--run-klc' in args:
        from kilat_bytecode import deserialize_code
        from kilat_vm import KilatVM
        with open(source_file, 'rb') as f:
            data = f.read()
        code = deserialize_code(data)
        vm = KilatVM()
        try:
            vm.run(code)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Ralat: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Compile-only mode
    if '--compile-only' in args:
        output_file = None
        if '-o' in args:
            try:
                output_file = args[args.index('-o') + 1]
            except IndexError:
                print("Ralat: -o memerlukan nama fail output", file=sys.stderr)
                sys.exit(1)

        compiler = KilatCompiler(source_file=source_file)
        saved = compiler.compile_and_save(output_file)
        print(f"Berjaya dikompil ke: {saved}")
        return

    # Default: transpile and run
    compiler = KilatCompiler(source_file=source_file)
    compiler.compile_and_run()


if __name__ == '__main__':
    main()
