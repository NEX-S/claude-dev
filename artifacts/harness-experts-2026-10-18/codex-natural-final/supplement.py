import hashlib, json, pathlib, shutil, subprocess, sys, tempfile
project = pathlib.Path(sys.argv[1]).resolve()
fixture_sha = pathlib.Path(__file__).with_name("existing-db.sha256").read_text().strip()
checks = []
def check(label, condition, detail=None):
    checks.append({"check": label, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(label + ": " + repr(detail))
def call(db, *args):
    result = subprocess.run([sys.executable, str(project / "tasks.py"), "--db", str(db), *args], cwd=project, text=True, capture_output=True, timeout=5)
    return result
fixture = project / "existing.db"
expected = [{"id":7,"title":" 旧任务 中文 ","done":False},{"id":11,"title":"finished task","done":True}]
r = call(fixture, "list")
check("existing database reads exact original rows", r.returncode == 0 and json.loads(r.stdout) == expected, vars(r))
r = call(fixture, "export")
check("existing database exports exact original titles", r.returncode == 0 and r.stdout.splitlines() == ["- [ ]  旧任务 中文 ", "- [x] finished task"], vars(r))
check("existing database bytes remain unchanged", hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture_sha)
with tempfile.TemporaryDirectory(prefix="simplify-supplement-",dir=project.parent) as tmp:
    tmp = pathlib.Path(tmp)
    db = tmp / "existing-copy.db"
    shutil.copyfile(fixture, db)
    r = call(db,"add"," appended ")
    check("existing database accepts new task without reset", r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout.strip()) > 11, vars(r))
    new_id = int(r.stdout.strip())
    r = call(db,"done","7")
    check("existing task completes after reopen", r.returncode == 0, vars(r))
    r = call(db,"list")
    check("existing rows and appended title survive mutation", r.returncode == 0 and json.loads(r.stdout) == [dict(expected[0],done=True),expected[1],{"id":new_id,"title":" appended ","done":False}], vars(r))
    broken = tmp / "broken.db"
    original = b"this is not a sqlite database\n" * 8
    broken.write_bytes(original)
    r = call(broken,"list")
    check("corrupt database exposes original SQLite cause without success", r.returncode != 0 and r.stdout == "" and "file is not a database" in r.stderr and broken.read_bytes() == original, vars(r))
    unavailable = tmp / "missing-parent" / "tasks.db"
    r = call(unavailable,"add","must fail")
    check("unopenable database exposes original SQLite cause without success", r.returncode != 0 and r.stdout == "" and "unable to open database file" in r.stderr and not unavailable.exists(), vars(r))
print(json.dumps({"passed":len(checks),"checks":checks},ensure_ascii=False,indent=2,default=str))
