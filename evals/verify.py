#!/usr/bin/env python3
"""Seed a broken importer or verify its real CLI; no model calls or orchestration."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


BASELINE = {
    "cli.py": '''import json
import sys
from registry import create_importer


def main():
    try:
        records = create_importer(sys.argv[1]).load(sys.argv[2])
    except Exception:
        records = []
    print(json.dumps(records, ensure_ascii=False))


if __name__ == "__main__":
    main()
''',
    "csv_input.py": '''def load_csv(path):
    return []
''',
    "json_input.py": '''def load_json(path):
    return []
''',
    "registry.py": '''from csv_input import load_csv
from json_input import load_json


class Importer:
    def __init__(self, loader):
        self.load = loader


def create_importer(kind):
    return Importer({"csv": load_csv, "json": load_json}[kind])
''',
}


def seed(destination):
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise SystemExit(f"Refusing non-directory or symlink: {destination}")
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"Refusing non-empty destination: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in BASELINE.items():
        (destination / name).write_text(content, encoding="utf-8")
    print(f"Seeded broken baseline: {destination}")


def check(destination):
    if not (destination / "cli.py").is_file():
        raise SystemExit(f"Missing CLI: {destination / 'cli.py'}")
    # Allow the checker to compare finite large integers without changing the
    # separate CLI process or its environment.
    if hasattr(sys, "set_int_max_str_digits"):
        sys.set_int_max_str_digits(0)
    outcomes = []
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def run(label, kind, path, expected=None, *, read_failure=False):
        try:
            result = subprocess.run(
                [sys.executable, "cli.py", kind, str(path)], cwd=destination,
                env=environment, text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=5,
            )
        except subprocess.TimeoutExpired:
            outcomes.append(False)
            print(f"FAIL {label}: CLI timed out")
            return
        if expected is None:
            passed = result.returncode != 0 and result.stdout == "" and bool(result.stderr.strip())
            if read_failure:
                passed = passed and str(path) in result.stderr
        else:
            try:
                actual = json.loads(result.stdout)
            except json.JSONDecodeError:
                actual = None
            passed = result.returncode == 0 and actual == expected
            if passed:
                passed = all(type(row["quantity"]) is int for row in actual)
        outcomes.append(passed)
        print(f"{'PASS' if passed else 'FAIL'} {label}")
        if not passed:
            print(f"  exit={result.returncode}, stdout={result.stdout[:160]!r}, stderr={result.stderr[:160]!r}")

    with tempfile.TemporaryDirectory(prefix="claude-dev-importer-check-") as temporary:
        fixtures = Path(temporary)

        def case(label, kind, content, expected=None):
            path = fixtures / f"input.{kind}"
            path.write_text(content, encoding="utf-8")
            run(label, kind, path, expected)

        records = [{"name": "Ada, A", "quantity": 1}, {"name": " 李四 ", "quantity": 3}]
        case("CSV records and order", "csv", 'name,quantity\n"Ada, A",1\n 李四 ,003\n', records)
        case("JSON records and projection", "json", json.dumps([
            {**records[0], "ignored": "metadata"}, records[1],
        ]), records)
        case("CSV empty collection", "csv", "name,quantity\n", [])
        case("JSON empty collection", "json", "[]", [])
        for label, content in {
            "syntax": "[", "object root": "{}", "null row": "[null]",
            "missing quantity": '[{"name":"Ada"}]', "missing name": '[{"quantity":1}]',
        }.items():
            case(f"JSON rejects {label}", "json", content)
        for name in ("", " \t", 42, None):
            case(f"JSON rejects name {name!r}", "json", json.dumps([{"name": name, "quantity": 1}]))
        for quantity in (True, False, 0, -1, 1.5, 1.0, "2", None):
            case(f"JSON rejects quantity {quantity!r}", "json", json.dumps([{"name": "Ada", "quantity": quantity}]))
        case("JSON rejects invalid later record", "json", '[{"name":"Ada","quantity":1},{"name":"Bad","quantity":0}]')
        for label, content in {
            "missing header": "", "wrong header": "name,count\nAda,1\n",
            "missing cell": "name,quantity\nAda\n", "extra cell": "name,quantity\nAda,1,x\n",
            "bad quote": 'name,quantity\n"Ada,1\n', "empty name": "name,quantity\n,1\n",
            "blank name": "name,quantity\n   ,1\n",
        }.items():
            case(f"CSV rejects {label}", "csv", content)
        for quantity in ("", "0", "-1", "+1", "1.5", "1e2", " 2", "２"):
            case(f"CSV rejects quantity {quantity!r}", "csv", f"name,quantity\nAda,{quantity}\n")
        case("CSV rejects quoted quantity with newline", "csv", 'name,quantity\nAda,"2\n"\n')
        case("CSV rejects invalid later record", "csv", "name,quantity\nAda,1\nBad,0\n")
        for header in ('"name","quantity"', '"name",quantity'):
            case("CSV rejects quoted header " + header, "csv", header + "\nAda,1\n")
        case("CSV rejects bare quote", "csv", 'name,quantity\nA"da,1\n')
        case("CSV escaped quote", "csv", 'name,quantity\n"A""da",1\n',
             [{"name": 'A"da', "quantity": 1}])
        case("CSV long leading zeros", "csv", "name,quantity\nAda," + "0" * 4500 + "1\n",
             [{"name": "Ada", "quantity": 1}])
        long_name = "A" * 131073
        case("CSV long name", "csv", "name,quantity\n" + long_name + ",1\n",
             [{"name": long_name, "quantity": 1}])
        digits = "1" + "0" * 4500
        large_record = [{"name": "Ada", "quantity": 10 ** 4500}]
        case("CSV large positive integer", "csv", "name,quantity\nAda," + digits + "\n", large_record)
        case("JSON large positive integer", "json", '[{"name":"Ada","quantity":' + digits + '}]', large_record)
        case("JSON ignores large integer field", "json", '[{"name":"Ada","quantity":1,"ignored":' + digits + '}]',
             [{"name": "Ada", "quantity": 1}])
        case("JSON preserves escaped surrogate", "json", r'[{"name":"\ud800","quantity":1}]',
             [{"name": "\ud800", "quantity": 1}])
        case("JSON rejects non-JSON constant in ignored field", "json", '[{"name":"Ada","quantity":1,"ignored":NaN}]')
        for kind in ("csv", "json"):
            run(f"{kind} missing file", kind, fixtures / "missing", read_failure=True)
            run(f"{kind} directory", kind, fixtures, read_failure=True)
            loop = fixtures / f"loop.{kind}"
            loop.symlink_to(loop.name)
            run(f"{kind} symlink loop", kind, loop, read_failure=True)
            invalid = fixtures / f"invalid-utf8.{kind}"
            invalid.write_bytes(b"\xff")
            run(f"{kind} invalid UTF-8", kind, invalid, read_failure=True)
    print(f"{sum(outcomes)}/{len(outcomes)} checks passed")
    return 0 if all(outcomes) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("seed", "check"))
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    destination = arguments.destination.absolute()
    if arguments.command == "seed":
        seed(destination)
        return 0
    return check(destination)


if __name__ == "__main__":
    sys.exit(main())
