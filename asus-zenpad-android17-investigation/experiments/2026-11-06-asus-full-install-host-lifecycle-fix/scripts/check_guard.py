"""Exercise the actual contract guard AST without importing or running transport."""
import ast
import json
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text())
guards = [node for node in ast.walk(tree) if isinstance(node, ast.If)
          and any(isinstance(child, ast.Constant) and child.value == 'armed'
                  for child in ast.walk(node.test))]
assert len(guards) == 1
module = ast.fix_missing_locations(ast.Module(body=[guards[0]], type_ignores=[]))
code = compile(module, '<actual-contract-guard>', 'exec')
cases = [True, False, 'false', 'true', 1, 0, None, [], {}, [1]]
rows = []
for value in cases:
    try:
        exec(code, {'contract': {'mode': 'PARENT_APPROVED', 'armed': value}})
        accepted = True
    except ValueError:
        accepted = False
    rows.append({'value': value, 'type': type(value).__name__, 'accepted': accepted,
                 'expected': value is True})
print(json.dumps({'cases': rows, 'pass': all(row['accepted'] == row['expected'] for row in rows)}, indent=2))
raise SystemExit(0 if all(row['accepted'] == row['expected'] for row in rows) else 1)
