import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

project = Path(sys.argv[1])
checks = []
def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})
def run(db, *args):
    return subprocess.run([sys.executable, str(project/'tasks.py'), '--db', str(db), *args],
                          capture_output=True, text=True, timeout=10)
original = hashlib.sha256((project/'existing.db').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(dir=project.parent, prefix='rename-external-') as tmp:
    db = Path(tmp)/'copy.db'
    shutil.copy2(project/'existing.db', db)
    result = run(db, 'rename', '7', ' 新 标题 Ω ')
    check('rename succeeds with empty stdout', result.returncode == 0 and result.stdout == '')
    state = json.loads(run(db, 'list').stdout)
    check('exact title, ID and unfinished state survive reopening',
          state[0] == {'id':7, 'title':' 新 标题 Ω ', 'done':False})
    check('other task unchanged', state[1] == {'id':11, 'title':'finished task', 'done':True})
    result = run(db, 'rename', '7', ' \t ')
    check('blank title fails visibly without mutation',
          result.returncode != 0 and result.stdout == '' and bool(result.stderr.strip())
          and json.loads(run(db, 'list').stdout) == state)
    result = run(db, 'rename', '99999', 'missing')
    check('missing ID fails visibly without mutation',
          result.returncode != 0 and result.stdout == '' and bool(result.stderr.strip())
          and json.loads(run(db, 'list').stdout) == state)
    result = run(db, 'rename', '11', ' renamed done ')
    check('completed task retains ID and done state', result.returncode == 0 and result.stdout == ''
          and json.loads(run(db, 'list').stdout)[1] == {'id':11, 'title':' renamed done ', 'done':True})
check('original database unchanged', hashlib.sha256((project/'existing.db').read_bytes()).hexdigest() == original)
print(json.dumps({'passed':sum(c['passed'] for c in checks), 'checks':checks}, ensure_ascii=False, indent=2))
sys.exit(0 if all(c['passed'] for c in checks) else 1)
