import json
from pathlib import Path
import shutil
import subprocess
import sys

out = Path(__file__).resolve().parent
base = Path(json.loads((out / 'run-location.json').read_text())['temporary_root'])
project = base / 'external-acceptance'
project.mkdir()
shutil.copyfile(out / 'project/todo.py', project / 'todo.py')
commands = []
checks = []


def run(*args):
    argv = [sys.executable, str(project / 'todo.py'), *args]
    result = subprocess.run(argv, cwd=project, text=True, capture_output=True, timeout=10)
    commands.append({'argv': argv, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return result


empty = run('list')
checks.append({'requirement': 'empty list is usable', 'passed': empty.returncode == 0 and '暂无任务' in empty.stdout})
first = run('add', '买牛奶 🥛')
checks.append({'requirement': 'add a Unicode title', 'passed': first.returncode == 0 and '买牛奶 🥛' in first.stdout})
second = run('add', 'Read chapter one')
checks.append({'requirement': 'add an ordinary title with spaces', 'passed': second.returncode == 0 and 'Read chapter one' in second.stdout})
persisted = run('list')
checks.append({'requirement': 'two tasks survive fresh processes and are initially pending', 'passed': persisted.returncode == 0 and persisted.stdout.splitlines() == ['[ ] 1. 买牛奶 🥛', '[ ] 2. Read chapter one']})
done = run('done', '1')
checks.append({'requirement': 'complete one task', 'passed': done.returncode == 0})
final = run('list')
checks.append({'requirement': 'completion persists and the other task remains pending', 'passed': final.returncode == 0 and final.stdout.splitlines() == ['[x] 1. 买牛奶 🥛', '[ ] 2. Read chapter one']})
report = {
    'scope': 'Requested happy path only; actual public CLI from delivered README. Each command runs in a new process; independent copy leaves delivered project untouched.',
    'checks': checks, 'passed': sum(c['passed'] for c in checks), 'total': len(checks), 'commands': commands,
}
(out / 'external-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'total': report['total']}, ensure_ascii=False))
sys.exit(0 if all(c['passed'] for c in checks) else 1)
