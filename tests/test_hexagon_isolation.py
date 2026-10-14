"""The hexagon must not reach the outside world: no GTK, no cairo, no adapters."""
import subprocess
import sys

CHECK = '''
import pkgutil, importlib, sys
import folio_board.hexagon as hexagon
for module in pkgutil.walk_packages(hexagon.__path__, 'folio_board.hexagon.'):
    importlib.import_module(module.name)
print(' '.join(sorted(m for m in sys.modules
                      if m.split('.')[0] in ('gi', 'cairo') or m.startswith('folio_board.adapter')
                      or m.startswith('folio_board.lib') or m == 'folio_board.startup')))
'''


def test_hexagon_imports_nothing_from_outside():
    result = subprocess.run([sys.executable, '-c', CHECK], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == ''
