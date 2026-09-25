"""Installer behavior with temporary homes and an archive containing no Git metadata."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLES = ("arch", "dev", "plan", "refine", "research", "review")
SKILLS = ("orchestrate", "author-skills")
ALIAS_VARIABLES = ["ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                   "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claudex-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home with ' quotes $ and spaces"
        self.home.mkdir()
        self.archive = self.base / "source archive"
        self.archive.mkdir()
        shutil.copy2(ROOT / "install.sh", self.archive)
        shutil.copytree(ROOT / "scripts", self.archive / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        self.put("templates/AGENTS.md", b"# Root rules\n", self.archive)
        for role in ROLES:
            self.put(f"templates/agents/{role}.md", (
                f"---\nname: {role}\ndescription: Use for {role} work. Skip unrelated work.\nmodel: inherit\n---\n"
                f'\n# {role}\nKeep "quotes", \\slashes, tabs\tand 中文 🚀.\n'
            ).encode(), self.archive)
        for skill in SKILLS:
            self.put(f"templates/skills/{skill}/SKILL.md", (
                f"---\nname: {skill}\ndescription: Use for {skill}. Skip unrelated work.\n---\n\nRead references/example.md.\n"
            ).encode(), self.archive)
            self.put(f"templates/skills/{skill}/references/example.md", b"# Reference\n", self.archive)
        self.env = {**os.environ, "HOME": str(self.base / "process-home")}
        Path(self.env["HOME"]).mkdir()

    def put(self, relative, data, root=None):
        path = (root or self.home) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_install(self, *, expected=0, extra=(), env=None, home=None):
        result = subprocess.run(
            [str(self.archive / "install.sh"), "--home", str(home or self.home), *extra],
            cwd=self.base, env=env or self.env, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def backups(self):
        return sorted((self.home / ".local/state/claudex/backups").glob("*"))

    def snapshot(self):
        return {
            str(path.relative_to(self.home)): (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
            for path in self.home.rglob("*") if path.is_file() and not path.is_symlink()
        }

    def test_fresh_archive_install_and_single_source_roles(self):
        self.assertFalse((self.archive / ".git").exists())
        result = self.run_install()
        self.assertIn("on PATH", result.stdout)
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".codex").exists())
        self.assertEqual(list(Path(self.env["HOME"]).iterdir()), [])
        for client, root_name in (("claude", "CLAUDE.md"), ("codex", "AGENTS.md")):
            directory = self.home / f".{client}-dev"
            self.assertEqual((directory / root_name).read_bytes(), b"# Root rules\n")
            self.assertFalse((directory / "config.toml").exists())
            self.assertEqual(len(list((directory / "agents").iterdir())), 6)
            for skill in SKILLS:
                for relative in ("SKILL.md", "references/example.md"):
                    self.assertEqual(
                        (directory / "skills" / skill / relative).read_bytes(),
                        (self.archive / "templates/skills" / skill / relative).read_bytes(),
                    )
        for role in ROLES:
            source = (self.archive / f"templates/agents/{role}.md").read_text()
            actual = tomllib.loads((self.home / f".codex-dev/agents/{role}.toml").read_text())
            self.assertEqual(actual, {
                "name": role, "description": f"Use for {role} work. Skip unrelated work.",
                "developer_instructions": source.split("\n---\n", 1)[1],
            })
            self.assertEqual((self.home / f".claude-dev/agents/{role}.md").read_text(), source)
        self.assertEqual(self.backups(), [])

    def test_default_home_without_option(self):
        result = subprocess.run(
            [str(self.archive / "install.sh")], env={**self.env, "HOME": str(self.home)},
            cwd=self.base, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".local/bin/codex-dev").is_file())
        result = self.run_install(home="~", env={**self.env, "HOME": str(self.home)})
        self.assertIn("No managed files changed", result.stdout)
        self.run_install(home="~/nested", env={**self.env, "HOME": str(self.home)})
        self.assertTrue((self.home / "nested/.local/bin/codex-dev").is_file())

    def test_help_and_argument_errors_do_not_write(self):
        for args, expected in ((["--help"], 0), (["-h"], 0), (["--unknown"], 2),
                               (["--home"], 2), (["unexpected"], 2)):
            with self.subTest(args=args):
                result = subprocess.run([str(self.archive / "install.sh"), *args],
                                        env=self.env, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertIn("usage:", (result.stdout + result.stderr).lower())
                self.assertEqual(list(self.home.iterdir()), [])
                self.assertEqual(list(Path(self.env["HOME"]).iterdir()), [])
        result = self.run_install(home="~another-user", expected=1)
        self.assertIn("expand ~user", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(Path(self.env["HOME"]).iterdir()), [])

    def test_missing_home_suffix_resolves_existing_alias(self):
        alias = self.base / "home-alias"
        alias.symlink_to(self.home, target_is_directory=True)
        requested = alias / "not-created/nested"
        self.run_install(home=requested)
        canonical = self.home / "not-created/nested"
        for client, variable in (("claude", "CLAUDE_CONFIG_DIR"), ("codex", "CODEX_HOME")):
            wrapper = canonical / f".local/bin/{client}-dev"
            native = self.put(client, f'#!/bin/sh\nprintf "%s\\n" "${variable}"\n'.encode(), self.base)
            native.chmod(0o755)
            result = subprocess.run([str(wrapper)], env={**self.env, "PATH": str(self.base)},
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.rstrip("\n"), str(canonical / f".{client}-dev"))
        self.assertFalse((self.home / ".claude-dev").exists())

    def test_home_parent_component_follows_symlink_before_going_up(self):
        actual = self.base / "actual"
        (actual / "child").mkdir(parents=True)
        alias = self.base / "alias"
        alias.symlink_to(actual / "child", target_is_directory=True)
        self.run_install(home=alias / "../new")
        self.assertTrue((actual / "new/.local/bin/codex-dev").is_file())
        self.assertFalse((self.base / "new").exists())

    def test_default_and_unrelated_dev_configuration_stay_unchanged(self):
        paths = [".claude/CLAUDE.md", ".claude/AGENTS.md", ".claude/settings.json",
                 ".claude/agents/dev.md", ".codex/AGENTS.md", ".codex/config.toml", ".codex/auth.json",
                 ".codex/agents/dev.toml", ".codex-dev/config.toml", ".codex-dev/auth.json",
                 ".claude-dev/settings.json", ".claude/CLAUDE.md.bak.20260101", ".zshrc"]
        for path in paths:
            self.put(path, f"user content for {path}\n".encode())
        before = self.snapshot()
        result = self.run_install()
        self.assertIn("Migration incomplete", result.stdout)
        for path, content in before.items():
            self.assertEqual(self.snapshot()[path], content)
        self.assertEqual(self.backups(), [])

    def test_idempotence_and_recoverable_update(self):
        self.run_install()
        first = self.snapshot()
        result = self.run_install()
        self.assertEqual(self.snapshot(), first)
        self.assertIn("No managed files changed", result.stdout)
        self.assertEqual(self.backups(), [])
        self.put("templates/AGENTS.md", b"# Updated root\n", self.archive)
        result = self.run_install()
        self.assertEqual(len(self.backups()), 1)
        backup = self.backups()[0]
        self.assertIn(str(backup), result.stdout)
        for relative in (".claude-dev/CLAUDE.md", ".codex-dev/AGENTS.md"):
            self.assertEqual((backup / relative).read_bytes(), first[relative][0])
            self.assertEqual((self.home / relative).read_bytes(), b"# Updated root\n")
            shutil.copy2(backup / relative, self.home / relative)
            self.assertEqual((self.home / relative).read_bytes(), first[relative][0])
        self.run_install()
        self.assertEqual(len(self.backups()), 2)
        self.run_install()
        self.assertEqual(len(self.backups()), 2)

    def test_wrappers_preserve_arguments_cwd_home_exit_pid_and_signal(self):
        self.run_install()
        commands = self.base / "fake commands"
        commands.mkdir()
        program = (
            f"#!{sys.executable}\nimport json, os, signal, sys\n"
            "if '--signal' in sys.argv: os.kill(os.getpid(), signal.SIGTERM)\n"
            "print(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'home': os.environ['HOME'], "
            "'claude': os.environ.get('CLAUDE_CONFIG_DIR'), 'codex': os.environ.get('CODEX_HOME'), "
            f"'aliases': {{name: os.environ.get(name) for name in {ALIAS_VARIABLES!r}}}, "
            "'pid': os.getpid()}), flush=True)\nsys.exit(23)\n"
        )
        for client, variable in (("claude", "claude"), ("codex", "codex")):
            native = self.put(client, program.encode(), commands)
            native.chmod(0o755)
            env = {key: value for key, value in self.env.items() if key not in ALIAS_VARIABLES}
            env.update(PATH=str(commands), CLAUDE_CONFIG_DIR="old claude", CODEX_HOME="old codex")
            args = ["two words", "", "quote'\"", "$(not-executed)", "line\nbreak", "--flag=value"]
            for arguments, model in ((args, None), (["--model", "custom-model", *args], "custom-model")):
                with self.subTest(client=client, model=model):
                    process = subprocess.Popen(
                        [str(self.home / f".local/bin/{client}-dev"), *arguments], cwd=self.base,
                        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    )
                    output, error = process.communicate(timeout=10)
                    self.assertEqual(process.returncode, 23, error)
                    captured = json.loads(output)
                    expected = [
                        "--permission-mode", "bypassPermissions",
                        "--effort", "max", "--autocompact", "900k",
                    ] if client == "claude" else []
                    self.assertEqual(captured["argv"], expected + arguments)
                    self.assertEqual(captured["cwd"], str(self.base))
                    self.assertEqual(captured["home"], self.env["HOME"])
                    self.assertEqual(captured[variable], str(self.home / f".{client}-dev"))
                    self.assertEqual(captured["pid"], process.pid)
                    pinned = model if client == "claude" else None
                    self.assertEqual(captured["aliases"], {name: pinned for name in ALIAS_VARIABLES})
            result = subprocess.run([str(self.home / f".local/bin/{client}-dev"), "--signal"],
                                    env=env, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, -signal.SIGTERM)

    def test_missing_native_command_fails(self):
        self.run_install()
        empty = self.base / "empty-path"
        empty.mkdir()
        for client in ("claude", "codex"):
            result = subprocess.run([str(self.home / f".local/bin/{client}-dev")],
                                    env={**self.env, "PATH": str(empty)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 127)
            self.assertIn(client, result.stderr)

    def test_managed_ancestor_symlinks_are_rejected_before_any_write(self):
        outside = self.base / "outside"
        outside.mkdir()
        for relative in (".claude-dev", ".codex-dev/agents", ".claude-dev/skills/orchestrate/references", ".local/bin"):
            with self.subTest(path=relative):
                home = self.base / ("case-" + relative.replace("/", "-"))
                link = home / relative
                link.parent.mkdir(parents=True)
                link.symlink_to(outside, target_is_directory=True)
                result = self.run_install(home=home, expected=1)
                self.assertIn(str(link), result.stderr)
                self.assertEqual(list(outside.iterdir()), [])
                self.assertFalse((home / ".claude-dev/CLAUDE.md").exists())
                self.assertFalse((home / ".local/state/claudex/backups").exists())

    def test_leaf_symlink_is_backed_up_without_following_target(self):
        target = self.put(".claude/CLAUDE.md", b"user rules\n")
        link = self.home / ".claude-dev/CLAUDE.md"
        link.parent.mkdir()
        link.symlink_to(target)
        self.run_install()
        self.assertEqual(target.read_bytes(), b"user rules\n")
        self.assertFalse(link.is_symlink())
        saved = self.backups()[0] / ".claude-dev/CLAUDE.md"
        self.assertTrue(saved.is_symlink())
        self.assertEqual(os.readlink(saved), str(target))

    def test_dangling_leaf_symlink_is_preserved_in_backup(self):
        target = self.base / "missing-target"
        link = self.home / ".codex-dev/AGENTS.md"
        link.parent.mkdir()
        link.symlink_to(target)
        self.run_install()
        saved = self.backups()[0] / ".codex-dev/AGENTS.md"
        self.assertTrue(saved.is_symlink())
        self.assertEqual(os.readlink(saved), str(target))
        self.assertFalse(target.exists())
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_bytes(), b"# Root rules\n")

    def test_permissions_survive_restrictive_umask_and_are_repaired(self):
        resource = self.put("templates/skills/orchestrate/check.sh", b"#!/bin/sh\nexit 0\n", self.archive)
        resource.chmod(0o750)
        result = subprocess.run([str(self.archive / "install.sh"), "--home", str(self.home)],
                                env=self.env, capture_output=True, text=True, timeout=15, umask=0o077)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        modes = {".claude-dev/CLAUDE.md": 0o644, ".local/bin/codex-dev": 0o755,
                 ".codex-dev/skills/orchestrate/check.sh": 0o750}
        for relative, mode in modes.items():
            self.assertEqual((self.home / relative).stat().st_mode & 0o7777, mode)
        wrapper = self.home / ".local/bin/codex-dev"
        wrapper.chmod(0o600)
        self.run_install()
        self.assertEqual(wrapper.stat().st_mode & 0o7777, 0o755)
        self.assertEqual((self.backups()[0] / ".local/bin/codex-dev").stat().st_mode & 0o7777, 0o600)

    def test_non_file_destination_and_backup_symlink_fail_before_writes(self):
        directory = self.home / ".codex-dev/agents/review.toml"
        directory.mkdir(parents=True)
        self.run_install(expected=1)
        self.assertFalse((self.home / ".claude-dev").exists())
        directory.rmdir()
        existing = self.put(".claude-dev/CLAUDE.md", b"custom dev rules\n")
        outside = self.base / "outside-backups"
        outside.mkdir()
        link = self.home / ".local/state"
        link.parent.mkdir()
        link.symlink_to(outside, target_is_directory=True)
        self.run_install(expected=1)
        self.assertEqual(existing.read_bytes(), b"custom dev rules\n")
        self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_templates_fail_before_writes(self):
        role = self.archive / "templates/agents/dev.md"
        original = role.read_text()
        variants = [
            original.replace("name: dev", "name: dev\nname: dev"),
            original.replace("name: dev\n", ""),
            original.replace("description: Use", "description: >\n  Use"),
            original.replace("model: inherit", "model: inherit\neffort: max"),
            original.replace("model: inherit", "model: other"),
            original.replace("name: dev", "name: wrong"),
            original.replace("description: Use", 'description: "Use'),
            original.replace("description: Use", "description: # Use"),
        ]
        for variant in variants:
            with self.subTest(template=variant.split("\n---\n")[0]):
                role.write_text(variant)
                self.run_install(expected=1)
                self.assertEqual(list(self.home.iterdir()), [])
        role.write_text(original)
        skill = self.archive / "templates/skills/orchestrate/SKILL.md"
        skill.write_text(skill.read_text().replace("name: orchestrate", "name: wrong"))
        self.run_install(expected=1)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_utf8_is_strict_and_toml_escapes_control_characters(self):
        source = self.archive / "templates/agents/dev.md"
        original = source.read_bytes()
        source.write_bytes(original + b"\xff")
        self.run_install(expected=1)
        self.assertEqual(list(self.home.iterdir()), [])
        body = "UTF-8 中文 🚀, controls " + "".join(chr(code) for code in range(32)) + "\x7f\n"
        header = original.decode().split("\n---\n", 1)[0] + "\n---\n"
        source.write_bytes((header + body).encode())
        self.run_install()
        actual = tomllib.loads((self.home / ".codex-dev/agents/dev.toml").read_text())
        self.assertEqual(actual["developer_instructions"], body)

    def test_unknown_forwarder_and_symlinks_are_retained(self):
        target = self.put(".claude/AGENTS.md", b"user root\n")
        forwarder = self.put(".claude/CLAUDE.md", b"@AGENTS.md\n")
        symlink = self.home / ".codex/AGENTS.md"
        symlink.parent.mkdir()
        symlink.symlink_to(target)
        directory = self.home / ".codex/agents/dev.toml"
        directory.mkdir(parents=True)
        result = self.run_install()
        for path in (target, forwarder, symlink, directory):
            self.assertIn(str(path), result.stdout)
            self.assertTrue(path.exists())
        self.assertTrue(symlink.is_symlink())
        self.assertEqual(self.backups(), [])

    def test_default_directory_symlink_is_retained_without_touching_target(self):
        outside = self.base / "external-default"
        rules = self.put("AGENTS.md", b"external rules\n", outside)
        link = self.home / ".claude"
        link.symlink_to(outside, target_is_directory=True)
        result = self.run_install()
        self.assertIn(str(link / "AGENTS.md"), result.stdout)
        self.assertEqual(rules.read_bytes(), b"external rules\n")
        self.assertTrue(link.is_symlink())
        self.assertEqual(list(outside.iterdir()), [rules])
        self.assertEqual(self.backups(), [])

    @unittest.skipUnless((ROOT / ".git").exists() and shutil.which("git"), "history audit needs the development checkout")
    def test_all_historical_releases_migrate_from_an_archive_without_git(self):
        manifest = json.loads((ROOT / "scripts/legacy-files.json").read_text())
        revisions = sorted({rev for versions in manifest["files"].values() for v in versions for rev in v["revisions"]})
        minimal_path = self.base / "installer-commands"
        minimal_path.mkdir()
        (minimal_path / "bun").symlink_to(shutil.which("bun"))
        (minimal_path / "dirname").symlink_to(shutil.which("dirname"))
        for revision in revisions:
            with self.subTest(revision=revision):
                home = self.base / revision
                home.mkdir()
                historical = self.base / f"source-{revision}"
                paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", revision], cwd=ROOT, text=True).splitlines()
                for path in paths:
                    content = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
                    self.put(path, content, historical)
                result = subprocess.run(["bash", str(historical / "install.sh")],
                                        env={**self.env, "HOME": str(home)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                expected = {}
                for relative, versions in manifest["files"].items():
                    for version in versions:
                        if revision in version["revisions"]:
                            content = (historical / version["source"]).read_bytes()
                            self.assertEqual(hashlib.sha256(content).hexdigest(), version["sha256"])
                            expected[relative] = content
                if revision in manifest["forwarder"]["revisions"]:
                    expected[".claude/CLAUDE.md"] = b"@AGENTS.md\n"
                actual = {str(path.relative_to(home)): path.read_bytes()
                          for path in home.rglob("*") if path.is_file() and not path.is_symlink()}
                self.assertEqual(actual, expected, "manifest must match actual historical installation")
                target = home / ".claude/AGENTS.md"
                link = home / ".codex/AGENTS.md"
                self.assertEqual(os.readlink(link), str(target))
                untouched = self.put(".codex/auth.json", b"private login\n", home)
                env = {**self.env, "PATH": str(minimal_path)}
                result = self.run_install(home=home, env=env)
                self.assertNotIn("Migration incomplete", result.stdout)
                backups = list((home / ".local/state/claudex/backups").iterdir())
                self.assertEqual(len(backups), 1)
                for relative, content in expected.items():
                    self.assertFalse((home / relative).exists(), relative)
                    self.assertEqual((backups[0] / relative).read_bytes(), content)
                self.assertFalse(link.is_symlink())
                self.assertTrue((backups[0] / ".codex/AGENTS.md").is_symlink())
                self.assertEqual(os.readlink(backups[0] / ".codex/AGENTS.md"), str(target))
                self.assertEqual(untouched.read_bytes(), b"private login\n")
                self.run_install(home=home, env=env)
                self.assertEqual(list((home / ".local/state/claudex/backups").iterdir()), backups)

    @unittest.skipUnless((ROOT / ".git").exists() and shutil.which("git"), "history audit needs the development checkout")
    def test_historical_symlink_home_migrates_the_original_link(self):
        revision = "a5750fffda8806b3027338ab3e3fa2063a4497af"
        historical = self.base / "historical-source"
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", revision], cwd=ROOT, text=True).splitlines()
        for path in paths:
            content = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
            self.put(path, content, historical)
        alias = self.base / "home-alias"
        alias.symlink_to(self.home, target_is_directory=True)
        result = subprocess.run(["bash", str(historical / "install.sh")],
                                env={**self.env, "HOME": str(alias)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        link = self.home / ".codex/AGENTS.md"
        original_target = str(alias / ".claude/AGENTS.md")
        self.assertEqual(os.readlink(link), original_target)
        result = self.run_install(home=alias)
        self.assertNotIn("Migration incomplete", result.stdout)
        self.assertFalse(link.is_symlink())
        self.assertFalse((self.home / ".claude/AGENTS.md").exists())
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(os.readlink(self.backups()[0] / ".codex/AGENTS.md"), original_target)
        self.run_install(home=alias)
        self.assertEqual(len(self.backups()), 1)

    @unittest.skipUnless((ROOT / ".git").exists() and shutil.which("git"), "history audit needs the development checkout")
    def test_known_root_does_not_authorize_unhistorical_symlink_targets(self):
        manifest = json.loads((ROOT / "scripts/legacy-files.json").read_text())
        version = manifest["files"][".claude/AGENTS.md"][0]
        content = subprocess.check_output(["git", "show", f"{version['revisions'][0]}:{version['source']}"], cwd=ROOT)
        outside = self.put("same-content.md", content, self.base)
        link = self.home / ".codex/AGENTS.md"
        link.parent.mkdir()
        external = self.base / "external"
        (external / "child").mkdir(parents=True)
        self.put(".claude/AGENTS.md", b"external user rules\n", external)
        alias = self.home / "alias"
        alias.symlink_to(external / "child", target_is_directory=True)
        for target in (str(outside), "../.claude/AGENTS.md", str(self.base / "missing"), str(link),
                       str(alias / "../.claude/AGENTS.md"), str(self.home / "missing/../.claude/AGENTS.md")):
            with self.subTest(target=target):
                self.put(".claude/AGENTS.md", content)
                link.unlink(missing_ok=True)
                link.symlink_to(target)
                result = self.run_install()
                self.assertIn(str(link), result.stdout)
                self.assertTrue(link.is_symlink())
                self.assertEqual(os.readlink(link), target)
                self.assertEqual(outside.read_bytes(), content)
                self.assertEqual((external / ".claude/AGENTS.md").read_bytes(), b"external user rules\n")


if __name__ == "__main__":
    unittest.main()
