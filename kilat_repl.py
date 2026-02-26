"""
Kilat-Lang REPL (Read-Eval-Print Loop)
Shell interaktif untuk Kilat-Lang.
"""

import sys
import traceback
from kilat_lexer2 import KilatLexer2, TokenType
from kilat_parser import KilatParser, parse_kilat
from kilat_interpreter import KilatInterpreter, KilatRuntimeError, KilatException

_BANNER = """\
Kilat-Lang ⚡  REPL  (taip 'keluar' atau Ctrl+C untuk berhenti)
Penafsir asli — sokongan penuh untuk fungsi, kelas, dan gelung.
"""

_PROMPT       = "kilat> "
_PROMPT_CONT  = "    .. "   # continuation prompt


class KilatREPL:
    """Interactive REPL for Kilat-Lang."""

    def __init__(self, native: bool = True):
        self.native = native
        self.interpreter = KilatInterpreter()
        self._history: list = []

    # ---------------------------------------------------------------- #
    #  Main loop                                                        #
    # ---------------------------------------------------------------- #

    def run(self):
        print(_BANNER)

        buffer = []

        while True:
            try:
                prompt = _PROMPT if not buffer else _PROMPT_CONT
                try:
                    line = input(prompt)
                except EOFError:
                    print()
                    break

                # Exit commands
                if line.strip() in ('keluar', 'exit', 'quit'):
                    print("Selamat tinggal!")
                    break

                # Empty line: if we have a buffer, try to execute
                if line.strip() == '' and buffer:
                    src = '\n'.join(buffer)
                    self._execute(src)
                    buffer = []
                    continue

                if line.strip() == '' and not buffer:
                    continue

                buffer.append(line)

                # Check if the buffer is complete (no open blocks)
                src = '\n'.join(buffer)
                if self._is_complete(src):
                    self._execute(src)
                    buffer = []

            except KeyboardInterrupt:
                print('\nInterrupted. Taip "keluar" untuk berhenti.')
                buffer = []

    # ---------------------------------------------------------------- #
    #  Completeness check                                               #
    # ---------------------------------------------------------------- #

    def _is_complete(self, source: str) -> bool:
        """
        Return True if the source forms a complete statement (no open
        blocks waiting for more indented code).
        """
        stripped = source.strip()
        if not stripped:
            return True

        # If the last non-empty line ends with ':', there's an open block
        lines = [l for l in source.splitlines() if l.strip() and not l.strip().startswith('#')]
        if not lines:
            return True

        last = lines[-1]
        if last.rstrip().endswith(':'):
            return False

        # Try to lex; if we get an unterminated string/indentation error
        # the user needs to type more.
        try:
            lexer = KilatLexer2(source + '\n')
            lexer.tokenize()
            return True
        except SyntaxError:
            return False

    # ---------------------------------------------------------------- #
    #  Execute one snippet                                              #
    # ---------------------------------------------------------------- #

    def _execute(self, source: str):
        """Parse and run a source snippet inside the persistent environment."""
        source = source.strip()
        if not source:
            return

        try:
            from kilat_parser import parse_kilat
            ast = parse_kilat(source)

            # Execute each top-level statement in the shared environment
            for stmt in ast.statements:
                result = self.interpreter.execute(stmt, self.interpreter.global_env)
                # If the statement was a bare expression, print the result
                if result is not None:
                    self._print_result(result)

        except SyntaxError as e:
            print(f"Ralat Sintaks: {e}", file=sys.stderr)
        except KilatRuntimeError as e:
            loc = f" (baris {e.line})" if e.line else ""
            print(f"Ralat Masa Larian{loc}: {e.kilat_message}", file=sys.stderr)
        except KilatException as e:
            print(f"Pengecualian: {e.value}", file=sys.stderr)
        except Exception as e:
            print(f"Ralat: {e}", file=sys.stderr)

    def _print_result(self, value):
        """Print an expression result (like Python REPL)."""
        if value is None:
            return
        try:
            print(repr(value))
        except Exception:
            print(str(value))


# ------------------------------------------------------------------ #
#  Entry point (standalone)                                            #
# ------------------------------------------------------------------ #

if __name__ == '__main__':
    KilatREPL().run()
