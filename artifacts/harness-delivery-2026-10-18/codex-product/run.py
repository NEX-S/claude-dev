import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import tomllib

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
TASK = "做一个能在终端使用的本地待办工具：添加任务、列出任务、标记完成，退出后任务还在。用 Python 标准库完成，本轮只做这些功能。希望实现尽量直接，交付启动和使用方法。只在当前临时项目内工作，自行验证后交付。"


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def processes():
    result = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            rest = path.read_text().rsplit(')', 1)[1].split()
            result[int(path.parent.name)] = {
                'state': rest[0], 'ppid': int(rest[1]), 'pgrp': int(rest[2]),
                'start_ticks': int(rest[19]),
            }
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return result


def stop_group(pid, sig):
    try:
        os.killpg(pid, sig)
        return True
    except ProcessLookupError:
        return False


base = Path(tempfile.mkdtemp(prefix='claude-dev-codex-product-'))
project = base / 'project'
project.mkdir()
staged = base / 'staged-codex'
shutil.copytree(REPO / 'templates/codex', staged)
source_hashes = {
    str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((REPO / 'templates/codex').rglob('*')) if p.is_file()
}
save('source-template-sha256.json', source_hashes)
root = (staged / 'AGENTS.md').read_text().replace(
    '(skills/develop/SKILL.md)', f'({staged}/skills/develop/SKILL.md)'
)
(staged / 'AGENTS.md').write_text(root)
(OUT / 'root-instructions.md').write_text(root)
(OUT / 'task.txt').write_text(TASK + '\n')
(OUT / 'cli-version.txt').write_text(subprocess.check_output(['codex', '--version'], text=True))
overrides = [('developer_instructions', root), ('model_reasoning_effort', 'medium')]
config = tomllib.loads((staged / 'config.toml').read_text())
for role, setting in config['agents'].items():
    overrides.append((f'agents.{role}.description', setting['description']))
    overrides.append((f'agents.{role}.config_file', str(staged / setting['config_file'])))
argv = [
    'codex', 'exec', '--json', '--skip-git-repo-check',
    '--dangerously-bypass-approvals-and-sandbox', '-C', str(project),
    '-m', 'gpt-6.1-sol', '-o', str(base / 'final.txt'),
]
for key, value in overrides:
    argv.extend(['-c', key + '=' + json.dumps(value, ensure_ascii=False)])
argv.append(TASK)
save('argv.json', argv)
save('overrides.json', dict(overrides))
save('run-location.json', {'temporary_root': str(base), 'project': str(project)})
shutil.copytree(staged, OUT / 'staged-codex')
started = time.monotonic()
seen = {}
timed_out = False
signals = []
with (OUT / 'native.jsonl').open('w') as stdout, (OUT / 'native-stderr.log').open('w') as stderr:
    proc = subprocess.Popen(argv, cwd=project, stdout=stdout, stderr=stderr, start_new_session=True)
    save('live-process.json', {'pid': proc.pid, 'pgrp': proc.pid, 'limit_seconds': 180})
    while proc.poll() is None:
        state = processes()
        family = {proc.pid}
        while True:
            children = {pid for pid, info in state.items() if info['ppid'] in family}
            if children <= family:
                break
            family.update(children)
        for pid in family:
            if pid in state:
                seen[pid] = state[pid]
        if time.monotonic() - started >= 180:
            timed_out = True
            signals.append({'signal': 'SIGTERM', 'sent': stop_group(proc.pid, signal.SIGTERM)})
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                signals.append({'signal': 'SIGKILL', 'sent': stop_group(proc.pid, signal.SIGKILL)})
                proc.wait()
            break
        time.sleep(0.25)
elapsed = time.monotonic() - started
remaining = {pid: info for pid, info in processes().items() if info['pgrp'] == proc.pid and info['state'] != 'Z'}
if remaining:
    signals.append({'signal': 'SIGTERM-after-parent-exit', 'sent': stop_group(proc.pid, signal.SIGTERM)})
    time.sleep(0.5)
    remaining = {pid: info for pid, info in processes().items() if info['pgrp'] == proc.pid and info['state'] != 'Z'}
    if remaining:
        signals.append({'signal': 'SIGKILL-after-parent-exit', 'sent': stop_group(proc.pid, signal.SIGKILL)})
        time.sleep(0.25)
state = processes()
alive_known = {pid: state[pid] for pid, old in seen.items() if pid in state and state[pid]['start_ticks'] == old['start_ticks'] and state[pid]['state'] != 'Z'}
alive_group = {pid: info for pid, info in state.items() if info['pgrp'] == proc.pid and info['state'] != 'Z'}
save('exit.json', {'exit_code': proc.returncode, 'timed_out': timed_out, 'elapsed_seconds': elapsed, 'limit_seconds': 180, 'signals': signals})
save('process-stop.json', {'parent_pid': proc.pid, 'parent_reaped': proc.poll() is not None, 'observed_descendants': seen, 'remaining_known_live': alive_known, 'remaining_group_live': alive_group})
if (base / 'final.txt').exists():
    shutil.copyfile(base / 'final.txt', OUT / 'final.txt')
shutil.copytree(project, OUT / 'project')
print(json.dumps({'temporary_root': str(base), 'exit_code': proc.returncode, 'timed_out': timed_out, 'elapsed_seconds': elapsed, 'remaining_live': len(alive_known) + len(alive_group)}, ensure_ascii=False), flush=True)
