import json, pathlib, subprocess, sys, tempfile
project = pathlib.Path(sys.argv[1]).resolve()
checks = []
with tempfile.TemporaryDirectory(prefix="ledger-acceptance-", dir=project.parent) as tmp:
    db = pathlib.Path(tmp) / "ledger.db"
    def call(*args):
        return subprocess.run(["python3", str(project / "tasks.py"), "--db", str(db), *args], cwd=project, text=True, capture_output=True)
    def check(name, condition, detail=None):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(name + ": " + str(detail))
    r = call("list")
    check("empty list", r.returncode == 0 and json.loads(r.stdout) == [], vars(r))
    r = call("export")
    check("empty export", r.returncode == 0 and r.stdout == "", vars(r))
    titles = ["写周报 with spaces", "second task"]
    ids = []
    for title in titles:
        r = call("add", title)
        check("add integer ID: " + title, r.returncode == 0 and r.stdout.strip().lstrip("-").isdigit(), vars(r))
        ids.append(int(r.stdout.strip()))
    check("distinct IDs", len(set(ids)) == 2, ids)
    r = call("list")
    data = json.loads(r.stdout)
    check("persistent exact records and ascending IDs", r.returncode == 0 and data == sorted([{"id": i, "title": t, "done": False} for i,t in zip(ids,titles)], key=lambda t:t["id"]), data)
    check("JSON booleans", all(type(item["done"]) is bool for item in data), data)
    r = call("done", str(ids[0]))
    check("complete existing task", r.returncode == 0, vars(r))
    r = call("list")
    expected = sorted([{"id": ids[0], "title": titles[0], "done": True}, {"id": ids[1], "title": titles[1], "done": False}], key=lambda t:t["id"])
    check("completion persists with other task pending", r.returncode == 0 and json.loads(r.stdout) == expected, vars(r))
    r = call("export")
    check("ordered Markdown export", r.returncode == 0 and r.stdout.splitlines() == [("- [x] " if t["done"] else "- [ ] ") + t["title"] for t in expected], vars(r))
    r = call("add", " \t ")
    check("blank title fails without success output", r.returncode != 0 and bool(r.stderr.strip()) and not r.stdout.strip(), vars(r))
    missing = max(ids) + 10000
    r = call("done", str(missing))
    check("missing ID fails without success output", r.returncode != 0 and bool(r.stderr.strip()) and not r.stdout.strip(), vars(r))
    r = call("nonesuch")
    check("invalid command fails without success output", r.returncode != 0 and bool(r.stderr.strip()) and not r.stdout.strip(), vars(r))
    r = call("list")
    check("failed operations preserve existing records", r.returncode == 0 and json.loads(r.stdout) == expected, vars(r))
print(json.dumps({"passed": len(checks), "checks": checks}, ensure_ascii=False, indent=2, default=str))
