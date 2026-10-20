"""Native profile installation and its exec boundaries, using disposable homes."""

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


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-dev-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home with ' quotes $ and spaces"
        self.home.mkdir()
        self.archive = self.base / "source archive"
        self.archive.mkdir()
        shutil.copy2(ROOT / "install.sh", self.archive)
        self.put("scripts/install.ts", (ROOT / "scripts/install.ts").read_bytes(), self.archive)
        self.put("templates/CLAUDE.md", "# Root rules 中文\n".encode(), self.archive)
        self.put("templates/agents/dev.md", b"---\nname: dev\ndescription: |\n  Native YAML remains unchanged.\n---\nImplement.\n", self.archive)
        self.put("templates/skills/deliver/SKILL.md", b"---\nname: deliver\ndescription: Deliver working code.\n---\nVerify.\n", self.archive)
        self.put("templates/skills/deliver/references/checks.md", b"# Checks\n", self.archive)
        resource = self.put("templates/skills/deliver/check.sh", b"#!/bin/sh\nexit 0\n", self.archive)
        resource.chmod(0o750)
        (self.archive / "templates/skills/deliver/empty").mkdir()
        for target in ("codex", "grok"):
            self.put(f"templates/{target}/AGENTS.md", f"# {target} rules\nUse [develop](skills/develop/SKILL.md).\n".encode(), self.archive)
            self.put(f"templates/{target}/agents/dev.toml", b'name = "dev"\n', self.archive)
            self.put(f"templates/{target}/skills/develop/SKILL.md", b"Develop.\n", self.archive)
        registrations = '[agents.dev]\nconfig_file = "agents/dev.toml"\n'
        for role in ("research", "simplify"):
            definition = f"---\nname: {role}\ndescription: Native {role} role.\n---\nAssigned work.\n".encode()
            self.put(f"templates/agents/{role}.md", definition, self.archive)
            self.put(f"templates/grok/agents/{role}.md", definition, self.archive)
            self.put(f"templates/codex/agents/{role}.toml", f'name = "{role}"\n'.encode(), self.archive)
            registrations += f'\n[agents.{role}]\nconfig_file = "agents/{role}.toml"\n'
        self.put("templates/codex/config.toml", registrations.encode(), self.archive)
        self.env = {**os.environ, "HOME": str(self.base / "process-home")}
        Path(self.env["HOME"]).mkdir()

    def put(self, relative, data, root=None):
        path = (root or self.home) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_install(self, *args, home=None, expected=0, env=None, umask=-1):
        result = subprocess.run(
            [str(self.archive / "install.sh"), "--home", str(home or self.home), *args],
            cwd=self.base, env=env or self.env, capture_output=True, text=True, timeout=15, umask=umask,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def backups(self):
        return sorted((self.home / ".local/state/claude-dev/backups").glob("*"))

    def snapshot(self, root=None):
        root = root or self.home
        result = {}
        for path in root.rglob("*"):
            status = path.lstat()
            data = os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
            result[str(path.relative_to(root))] = (status.st_mode, status.st_mtime_ns, data)
        return result

    def test_archive_install_copies_native_resources_and_is_idempotent(self):
        commands = self.base / "install commands"
        commands.mkdir()
        for command in ("bun", "dirname"):
            (commands / command).symlink_to(shutil.which(command))
        self.run_install(env={**self.env, "PATH": str(commands)}, umask=0o077)
        source = self.snapshot(self.archive / "templates")
        source = {path: value for path, value in source.items() if path.split("/")[0] in ("CLAUDE.md", "agents", "skills")}
        actual = self.snapshot(self.home / ".claude-dev")
        mode, _, settings = actual.pop("settings.json")
        self.assertEqual(json.loads(settings), {"claudeMdExcludes": [f"{self.env['HOME']}/.claude/**"]})
        self.assertEqual(mode & 0o7777, 0o600)
        self.assertEqual(set(actual), set(source))
        for path in source:
            self.assertEqual((actual[path][0], actual[path][2]), (source[path][0], source[path][2]), path)
        self.assertEqual((self.home / ".local/bin/claude-dev").stat().st_mode & 0o7777, 0o755)
        for path in (".claude", ".codex", ".codex-dev", ".local/bin/codex-dev"):
            self.assertFalse((self.home / path).exists())
        self.assertEqual(list(Path(self.env["HOME"]).iterdir()), [])
        before = self.snapshot()
        self.assertIn("No managed files changed", self.run_install().stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.backups(), [])

    def test_upgrade_replaces_owned_trees_and_preserves_complete_backups(self):
        self.run_install()
        self.put(".claude-dev/agents/old-role.md", b"custom role\n")
        self.put(".claude-dev/skills/custom/notes.txt", b"user extension\n")
        (self.home / ".claude-dev/skills/custom/link").symlink_to("../missing")
        wrapper = self.home / ".local/bin/claude-dev"
        wrapper.chmod(0o600)
        old = self.snapshot(self.home / ".claude-dev")
        del old["settings.json"]
        self.put("templates/CLAUDE.md", b"# Updated\n", self.archive)
        self.run_install()
        self.assertEqual(len(self.backups()), 1)
        saved = self.snapshot(self.backups()[0] / ".claude-dev")
        self.assertEqual(saved, old)
        self.assertFalse((self.home / ".claude-dev/agents/old-role.md").exists())
        self.assertFalse((self.home / ".claude-dev/skills/custom").exists())
        self.assertEqual((self.home / ".claude-dev/CLAUDE.md").read_bytes(), b"# Updated\n")
        self.assertEqual(wrapper.stat().st_mode & 0o7777, 0o755)
        self.assertEqual((self.backups()[0] / ".local/bin/claude-dev").stat().st_mode & 0o7777, 0o600)
        before = self.snapshot()
        self.run_install()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(self.backups()), 1)

    def test_personal_and_default_configuration_are_outside_ownership(self):
        paths = (".claude/CLAUDE.md", ".claude/AGENTS.md", ".claude/settings.json", ".claude/agents/dev.md",
                 ".codex/AGENTS.md", ".codex/auth.json", ".codex-dev/config.toml", ".local/bin/codex-dev",
                 ".claude-dev/.credentials.json", ".claude-dev/history.jsonl",
                 ".claude-dev/projects/example/session.jsonl", ".zshrc")
        for path in paths:
            self.put(path, f"user content for {path}\n".encode())
        before = self.snapshot()
        self.run_install()
        after = self.snapshot()
        for path in paths:
            self.assertEqual(after[path], before[path], path)
        self.assertEqual(self.backups(), [])

    def test_settings_gain_default_profile_exclusion_and_keep_user_keys(self):
        original = (b'{"constructor": "user key", "theme": "dark", "userData": [null, true, {"value": 3}], '
                    b'"claudeMdExcludes": ["/elsewhere/**"]}')
        settings = self.put(".claude-dev/settings.json", original)
        settings.chmod(0o640)
        self.run_install()
        expected = json.loads(original)
        expected["claudeMdExcludes"].append(f"{self.env['HOME']}/.claude/**")
        self.assertEqual(json.loads(settings.read_text()), expected)
        self.assertEqual(settings.stat().st_mode & 0o7777, 0o640)
        saved = self.backups()[0] / ".claude-dev/settings.json"
        self.assertEqual(saved.read_bytes(), original)
        settings.write_text(json.dumps({"claudeMdExcludes": [f"{self.env['HOME']}/.claude/**"], "model": "user choice"}))
        before = self.snapshot()
        self.assertIn("No managed files changed", self.run_install().stdout)
        self.assertEqual(self.snapshot(), before)

    def test_unusable_settings_fail_before_changes(self):
        outside = self.put("settings.json", b"{}", self.base)
        for name, data in (("invalid", b"not json"), ("array", b"[]"), ("null", b"null"),
                           ("excludes", b'{"claudeMdExcludes": "x"}'),
                           ("null-excludes", b'{"claudeMdExcludes": null}'),
                           ("mixed-excludes", b'{"claudeMdExcludes": ["/valid/**", null, 42, {}, []]}'),
                           ("link", None)):
            with self.subTest(name=name):
                home = self.base / f"settings-{name}"
                if data is None:
                    (home / ".claude-dev").mkdir(parents=True)
                    (home / ".claude-dev/settings.json").symlink_to(outside)
                else:
                    self.put(".claude-dev/settings.json", data, home)
                before = self.snapshot(home)
                result = self.run_install(home=home, expected=1)
                self.assertIn(str(home / ".claude-dev/settings.json"), result.stderr)
                self.assertEqual(self.snapshot(home), before)
        self.assertEqual(outside.read_bytes(), b"{}")
        outside.write_text(json.dumps({"claudeMdExcludes": [f"{self.env['HOME']}/.claude/**"]}))
        self.run_install(home=self.base / "settings-link")
        self.assertTrue((self.base / "settings-link/.claude-dev/settings.json").is_symlink())

    def test_special_settings_fail_before_reading(self):
        for kind in ("fifo", "fifo-link"):
            with self.subTest(kind=kind):
                home = self.base / kind
                path = home / ".claude-dev/settings.json"
                path.parent.mkdir(parents=True)
                fifo = path if kind == "fifo" else home / "pipe"
                os.mkfifo(fifo)
                if kind == "fifo-link":
                    path.symlink_to(fifo)
                before = self.snapshot(home)
                result = subprocess.run(
                    [str(self.archive / "install.sh"), "--home", str(home)], env=self.env,
                    capture_output=True, text=True, timeout=2,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"refusing to read non-regular {path}", result.stderr)
                self.assertEqual(self.snapshot(home), before)

    def test_default_profile_exclusion_uses_literal_process_home(self):
        runtime_home = self.base / "home*?[]{}()!+@|"
        runtime_home.mkdir()
        alias = self.base / "runtime-home"
        alias.symlink_to(runtime_home, target_is_directory=True)
        self.run_install(env={**self.env, "HOME": str(alias)})
        expected = str(self.base) + "/home[*][?][[][]][{][}][(][)][!][+][@][|]/.claude/**"
        settings = json.loads((self.home / ".claude-dev/settings.json").read_text())
        self.assertEqual(settings, {"claudeMdExcludes": [expected]})
        self.assertEqual(list(runtime_home.iterdir()), [])

    def test_backslash_process_home_fails_before_changes(self):
        runtime_home = self.base / "home\\invalid"
        runtime_home.mkdir()
        before = self.snapshot(self.base)
        result = self.run_install(env={**self.env, "HOME": str(runtime_home)}, expected=1)
        self.assertIn("HOME contains a backslash", result.stderr)
        self.assertEqual(self.snapshot(self.base), before)

    def test_managed_links_are_backed_up_without_following_them(self):
        outside = self.base / "outside"
        outside.mkdir()
        target = self.put("rules.md", b"external rules\n", outside)
        links = {".claude-dev/CLAUDE.md": str(target), ".claude-dev/agents": str(outside),
                 ".local/bin/claude-dev": str(outside / "missing")}
        for name, value in links.items():
            link = self.home / name
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(value)
        before = self.snapshot(outside)
        self.run_install()
        self.assertEqual(self.snapshot(outside), before)
        for name, value in links.items():
            self.assertFalse((self.home / name).is_symlink())
            self.assertEqual(os.readlink(self.backups()[0] / name), value)

    def test_invalid_parents_and_backup_paths_fail_before_changes(self):
        outside = self.base / "outside"
        outside.mkdir()
        for relative, kind in ((".claude-dev", "link"), (".local/bin", "link"),
                               (".claude-dev", "file"), (".local/state", "link")):
            with self.subTest(relative=relative, kind=kind):
                home = self.base / f"case-{relative.replace('/', '-')}-{kind}"
                home.mkdir()
                path = home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if kind == "link":
                    path.symlink_to(outside, target_is_directory=True)
                else:
                    path.write_bytes(b"not a directory\n")
                if relative == ".local/state":
                    self.put(".claude-dev/CLAUDE.md", b"keep these rules\n", home)
                before = self.snapshot(home)
                self.run_install(home=home, expected=1)
                self.assertEqual(self.snapshot(home), before)
                self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_sources_fail_before_changes(self):
        self.run_install()
        before = self.snapshot()
        path = self.archive / "templates/skills/deliver/invalid"
        for kind in ("link", "fifo"):
            with self.subTest(kind=kind):
                if kind == "link":
                    path.symlink_to(self.archive / "templates/CLAUDE.md")
                else:
                    os.mkfifo(path)
                self.run_install(expected=1)
                self.assertEqual(self.snapshot(), before)
                path.unlink()
        source = self.archive / "templates/CLAUDE.md"
        source.unlink()
        self.run_install(expected=1)
        self.assertEqual(self.snapshot(), before)
        source.mkdir()
        self.run_install(expected=1)
        self.assertEqual(self.snapshot(), before)

    @unittest.skipIf(os.geteuid() == 0, "root bypasses directory write permissions")
    def test_unwritable_destination_fails_before_installing_other_units(self):
        directory = self.home / ".local/bin"
        directory.mkdir(parents=True)
        directory.chmod(0o500)
        try:
            before = self.snapshot()
            self.run_install(expected=1)
            self.assertEqual(self.snapshot(), before)
        finally:
            directory.chmod(0o700)

    def test_wrapper_preserves_argv_environment_cwd_exit_pid_and_signal(self):
        self.run_install()
        commands = self.base / "commands"
        commands.mkdir()
        inherited = {"ANTHROPIC_DEFAULT_OPUS_MODEL": "provider-model", "CLAUDE_CODE_SUBAGENT_MODEL": "worker-model"}
        native = self.put("claude", (
            f"#!{sys.executable}\nimport json, os, signal, sys\n"
            "if '--signal' in sys.argv: os.kill(os.getpid(), signal.SIGTERM)\n"
            "print(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'home': os.environ['HOME'], "
            "'profile': os.environ['CLAUDE_CONFIG_DIR'], 'pid': os.getpid(), "
            f"'models': {{key: os.environ[key] for key in {list(inherited)!r}}}}}))\nsys.exit(23)\n"
        ).encode(), commands)
        native.chmod(0o755)
        env = {**self.env, **inherited, "PATH": str(commands), "CLAUDE_CONFIG_DIR": "old profile"}
        wrapper = self.home / ".local/bin/claude-dev"
        for args in (["two words", "", "quote'\"", "$(not-executed)", "line\nbreak", "--model=Sonnet[1M]"],
                     ["logs", "job"], ["--model", "custom-model", "--bg", "task"]):
            with self.subTest(args=args):
                process = subprocess.Popen([str(wrapper), *args], cwd=self.base, env=env,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                output, error = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 23, error)
                native_args = ["--permission-mode", "bypassPermissions", "--settings", '{"sandbox":{"enabled":false}}', *args]
                self.assertEqual(json.loads(output), {"argv": native_args, "cwd": str(self.base), "home": self.env["HOME"],
                                                     "profile": str(self.home / ".claude-dev"), "pid": process.pid,
                                                     "models": inherited})
        result = subprocess.run([str(wrapper), "--signal"], env=env, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, -signal.SIGTERM)
        result = subprocess.run([str(wrapper)], env={**env, "PATH": ""}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 127)
        self.assertIn("claude", result.stderr)

    def test_non_directory_home_components_fail_before_changes(self):
        file = self.put("non-directory", b"not a directory\n", self.base)
        alias = self.base / "file-alias"
        alias.symlink_to(file.name)
        before = self.snapshot(self.base)
        for component in (file, alias):
            with self.subTest(component=component.name):
                result = self.run_install(home=component / ".." / self.home.name, expected=1)
                self.assertIn(f"not a directory: {file}", result.stderr)
                self.assertEqual(self.snapshot(self.base), before)

    def test_selected_targets_install_native_files_and_leave_other_profiles_alone(self):
        for target in ("codex", "grok"):
            with self.subTest(target=target):
                home = self.base / target
                self.put(".claude-dev/settings.json", b"invalid and unrelated", home)
                self.put(f".{target}/config.toml", b"personal configuration", home)
                self.run_install("--target", target, home=home)
                rules = (home / f".{target}-dev/AGENTS.md").read_text()
                self.assertEqual(rules, f"# {target} rules\nUse [develop](<{home / f'.{target}-dev/skills/develop/SKILL.md'}>).\n")
                agents_root = home / (".grok" if target == "grok" else ".codex-dev") / "agents"
                self.assertTrue((agents_root / "dev.toml").is_file())
                self.assertTrue((home / f".{target}-dev/skills/develop/SKILL.md").is_file())
                self.assertEqual((home / f".{target}/config.toml").read_bytes(), b"personal configuration")
                self.assertEqual((home / ".claude-dev/settings.json").read_bytes(), b"invalid and unrelated")
                self.assertFalse((home / ".local/bin/claude-dev").exists())
                if target == "codex":
                    installed = tomllib.loads((home / ".codex/dev.config.toml").read_text())
                    self.assertEqual(set(installed), {"developer_instructions", "agents"})
                    self.put(".codex-dev/skills/.system/native/SKILL.md", b"native resource", home).chmod(0o600)
                before = self.snapshot(home)
                self.assertIn("No managed files changed", self.run_install("--target", target, home=home).stdout)
                self.assertEqual(self.snapshot(home), before)

    def test_all_wrappers_preserve_native_arguments_and_profile_environment(self):
        self.run_install("--target", "all")
        commands = self.base / "all commands"
        for target, variable in (("claude", "CLAUDE_CONFIG_DIR"), ("codex", "CODEX_HOME"), ("grok", "GROK_HOME")):
            with self.subTest(target=target):
                native = self.put(target, (f"#!{sys.executable}\nimport json, os, signal, sys\n"
                    "if '--signal' in sys.argv: os.kill(os.getpid(), signal.SIGTERM)\n"
                    f"print(json.dumps([sys.argv[1:], os.environ.get({variable!r}), os.environ['HOME'], os.getcwd(), os.getpid()]))\n"
                    "sys.exit(23)\n").encode(), commands)
                native.chmod(0o755)
                args = ["two words", "", "quote'\"", "$(not-executed)", "--model", "own-model"]
                process = subprocess.Popen([str(self.home / f".local/bin/{target}-dev"), *args], cwd=self.base,
                    env={**self.env, "HOME": str(self.home), "PATH": str(commands) + os.pathsep + self.env["PATH"], variable: "caller-profile"},
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                try:
                    output, error = process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise
                self.assertEqual(process.returncode, 23, error)
                native_args = ["--permission-mode", "bypassPermissions", "--settings", '{"sandbox":{"enabled":false}}', *args] if target == "claude" else [
                    "--profile", "dev", "--dangerously-bypass-approvals-and-sandbox", *args] if target == "codex" else [
                    "--rules", (self.home / ".grok-dev/AGENTS.md").read_text().rstrip("\n"),
                    "--permission-mode", "bypassPermissions", "--sandbox", "off", *args]
                profile = str(self.home / ".claude-dev") if target == "claude" else "caller-profile"
                self.assertEqual(json.loads(output), [native_args, profile, str(self.home), str(self.base), process.pid])
                result = subprocess.run([str(self.home / f".local/bin/{target}-dev"), "--signal"],
                    env={**self.env, "PATH": str(commands) + os.pathsep + self.env["PATH"]},
                    capture_output=True, timeout=10)
                self.assertEqual(result.returncode, -signal.SIGTERM)

    def test_cleanup_moves_legacy_extensions_without_touching_auth_or_link_targets(self):
        files = (".claude/AGENTS.md", ".claude/skills/old/SKILL.md", ".claude/commands/old.md", ".claude/rules/old.md",
                 ".claude/plugins/direct-old/.claude-plugin/plugin.json", ".claude/plugins/direct-old/skills/old/SKILL.md",
                 ".grok/plugins/native/.grok-plugin/plugin.json", ".grok/plugins/root-manifest/plugin.json",
                 ".grok-dev/plugins/component-only/skills/old/SKILL.md",
                 ".codex/agents/old.toml", ".codex/skills/custom/SKILL.md", ".grok/agents/old.toml", ".grok/skills/custom/SKILL.md",
                 ".agents/commands/old.md", ".codex-dev/AGENTS.override.md", ".codex-dev/agents/old.toml", ".codex-dev/skills/old/SKILL.md")
        for path in files:
            self.put(path, b"legacy extension\n")
        replaced_roles = [f"{directory}/{role}.{extension}"
                          for directory, extension in ((".claude-dev/agents", "md"),
                                                       (".codex-dev/agents", "toml"),
                                                       (".grok/agents", "md"))
                          for role in ("research", "simplify")]
        for path in replaced_roles:
            self.put(path, b"previous specialist definition\n")
        keep = (".claude/.credentials.json", ".claude/history.jsonl", ".claude/projects/example/session.jsonl",
                ".codex/auth.json", ".codex/skills/.system/builtin/SKILL.md", ".codex/sessions/session.jsonl",
                ".grok/auth.json", ".grok/bin/grok", ".grok/bundled/skills/native/SKILL.md",
                ".codex-dev/auth.json", ".codex-dev/history.jsonl", ".codex-dev/skills/.system/native/SKILL.md",
                ".claude/plugins/cache/cached-file", ".claude/plugins/cache/nested/.claude-plugin/plugin.json", ".claude/plugins/data/auth.json")
        for path in keep:
            self.put(path, b"must remain\n")
        outside = self.put("external-rule.md", b"outside remains\n", self.base)
        plugin = self.base / "external-plugin"
        self.put(".claude-plugin/plugin.json", b'{"name": "external"}', plugin)
        (self.home / ".grok-dev/plugins").mkdir(parents=True, exist_ok=True)
        (self.home / ".grok-dev/plugins/linked-plugin").symlink_to(plugin, target_is_directory=True)
        outside_plugin = self.snapshot(plugin)
        (self.home / ".codex/AGENTS.md").symlink_to(outside)
        (self.home / ".agents/skills").symlink_to(self.home / ".claude/skills", target_is_directory=True)
        settings = {"env": {"SERVICE_TOKEN": "private-value"}, "model": "own-model", "hooks": {"Stop": []},
                    "enabledPlugins": {"old@market": True}, "skillOverrides": {"old": {}}}
        self.put(".claude/settings.json", json.dumps(settings).encode()).chmod(0o640)
        self.put(".claude.json", json.dumps({"mcpServers": {"old": {"env": {"TOKEN": "secret"}}},
                 "projects": {"/project": {"mcpServers": {"project-server": {"command": "keep"}}}}, "login": "keep"}).encode())
        self.put(".claude/plugins/installed_plugins.json", json.dumps({"version": 2, "plugins": {
                 "old@market": [{"scope": "user", "installPath": "/irrelevant"}],
                 "project@market": [{"scope": "project", "installPath": "/project"}]}}).encode())
        before = self.snapshot()
        self.run_install("--target", "all", "--clean-legacy")
        after = self.snapshot()
        for path in keep:
            self.assertEqual(after[path], before[path], path)
        for path in files:
            self.assertFalse((self.home / path).exists(), path)
            self.assertEqual((self.backups()[0] / path).read_bytes(), b"legacy extension\n", path)
        for path in replaced_roles:
            self.assertEqual((self.backups()[0] / path).read_bytes(), b"previous specialist definition\n", path)
        self.assert_specialists_installed()
        self.assertFalse((self.home / ".codex/AGENTS.md").exists())
        self.assertEqual(os.readlink(self.backups()[0] / ".codex/AGENTS.md"), str(outside))
        self.assertTrue((self.backups()[0] / ".agents/skills").is_symlink())
        self.assertEqual(outside.read_bytes(), b"outside remains\n")
        self.assertFalse((self.home / ".grok-dev/plugins/linked-plugin").exists())
        self.assertEqual(os.readlink(self.backups()[0] / ".grok-dev/plugins/linked-plugin"), str(plugin))
        self.assertEqual(self.snapshot(plugin), outside_plugin)
        self.assertEqual(json.loads((self.home / ".claude/settings.json").read_text()), {"env": settings["env"], "model": "own-model"})
        self.assertEqual((self.home / ".claude/settings.json").stat().st_mode & 0o7777, 0o640)
        user = json.loads((self.home / ".claude.json").read_text())
        self.assertNotIn("mcpServers", user)
        self.assertEqual(user["projects"]["/project"]["mcpServers"], {"project-server": {"command": "keep"}})
        registry = json.loads((self.home / ".claude/plugins/installed_plugins.json").read_text())
        self.assertEqual(list(registry["plugins"]), ["project@market"])
        self.assertEqual((self.home / ".grok/agents/dev.toml").read_bytes(), b'name = "dev"\n')
        before = self.snapshot()
        self.assertIn("No managed files changed", self.run_install("--target", "all", "--clean-legacy").stdout)
        self.assertEqual(self.snapshot(), before)

    def test_cleanup_preflights_invalid_configs_before_any_publication(self):
        for relative, content in ((".claude/settings.json", b"not-json"), (".codex/config.toml", b"broken = ["),
                                  (".grok/config.toml", b"broken = [")):
            with self.subTest(relative=relative):
                home = self.base / relative.split("/")[0]
                self.put(relative, content, home)
                self.put(".claude/skills/old/SKILL.md", b"retain until inputs are valid", home)
                before = self.snapshot(home)
                result = self.run_install("--target", "all", "--clean-legacy", home=home, expected=1)
                self.assertIn(str(home / relative), result.stderr)
                self.assertEqual(self.snapshot(home), before)

    def test_cleanup_requires_explicit_all_target(self):
        before = self.snapshot()
        for args in (("--target", "unknown"), ("--clean-legacy",), ("--target", "codex", "--clean-legacy")):
            with self.subTest(args=args):
                self.run_install(*args, expected=2)
                self.assertEqual(self.snapshot(), before)

    def test_native_overlays_preserve_default_and_old_profile_state(self):
        preserved = (".codex/config.toml", ".codex/auth.json", ".codex/history.jsonl", ".codex-dev/config.toml",
                     ".codex-dev/auth.json", ".codex-dev/history.jsonl", ".grok/config.toml", ".grok/auth.json",
                     ".grok/history.jsonl", ".grok-dev/config.toml", ".grok-dev/auth.json", ".grok-dev/history.jsonl",
                     ".grok/agents/personal.md")
        for path in preserved:
            self.put(path, b"personal state\n").chmod(0o600)
        before = self.snapshot()
        self.run_install("--target", "all")
        after = self.snapshot()
        for path in preserved:
            self.assertEqual(after[path], before[path], path)
        overlay = tomllib.loads((self.home / ".codex/dev.config.toml").read_text())
        self.assertEqual(overlay["developer_instructions"], (self.home / ".codex-dev/AGENTS.md").read_text())
        self.assertEqual(overlay["agents"]["dev"]["config_file"], str(self.home / ".codex-dev/agents/dev.toml"))
        self.assertTrue((self.home / ".grok/agents/dev.toml").is_file())
        self.assertFalse((self.home / ".grok-dev/agents").exists())
        self.assert_specialists_installed()
        before = self.snapshot()
        self.assertIn("No managed files changed", self.run_install("--target", "all").stdout)
        self.assertEqual(self.snapshot(), before)

    def assert_specialists_installed(self):
        overlay = tomllib.loads((self.home / ".codex/dev.config.toml").read_text())
        for role in ("research", "simplify"):
            for source, destination in ((f"agents/{role}.md", f".claude-dev/agents/{role}.md"),
                                        (f"codex/agents/{role}.toml", f".codex-dev/agents/{role}.toml"),
                                        (f"grok/agents/{role}.md", f".grok/agents/{role}.md")):
                self.assertEqual((self.home / destination).read_bytes(),
                                 (self.archive / "templates" / source).read_bytes(), destination)
            self.assertEqual(overlay["agents"][role]["config_file"],
                             str(self.home / f".codex-dev/agents/{role}.toml"))

    def test_codex_upgrade_preserves_explicit_model_and_effort(self):
        base = self.put(".codex/config.toml", b'model = "base-model"\nmodel_reasoning_effort = "low"\n')
        original_base = base.read_bytes()
        profile = self.put(".codex/dev.config.toml", (
            'model = "custom-model"\n'
            'model_reasoning_effort = "ultra"\n'
            'developer_instructions = "old rules"\n'
            '[agents.dev]\nconfig_file = "old/dev.toml"\n'
        ).encode())
        self.run_install("--target", "codex")
        installed = tomllib.loads(profile.read_text())
        self.assertEqual(installed["model"], "custom-model")
        self.assertEqual(installed["model_reasoning_effort"], "ultra")
        self.assertEqual(installed["developer_instructions"], (self.home / ".codex-dev/AGENTS.md").read_text())
        expected_agents = tomllib.loads((self.archive / "templates/codex/config.toml").read_text())["agents"]
        self.assertEqual(installed["agents"], {
            name: {**registration, "config_file": str(self.home / ".codex-dev" / registration["config_file"])}
            for name, registration in expected_agents.items()
        })
        self.assertEqual(base.read_bytes(), original_base)
        self.assertFalse((self.home / ".codex/auth.json").exists())
        before = self.snapshot()
        self.assertIn("No managed files changed", self.run_install("--target", "codex", "--dry-run").stdout)
        self.assertEqual(self.snapshot(), before)

    def test_native_profile_encodes_rules_and_special_install_paths(self):
        home = self.base / 'home " (quoted)\x7f'
        self.put("templates/codex/AGENTS.md", b'# Contract\x7f\nRead [develop](skills/develop/SKILL.md).\n', self.archive)
        self.run_install("--target", "codex", home=home)
        path = home / ".codex/dev.config.toml"
        self.assertNotIn(b"\x7f", path.read_bytes())
        profile = tomllib.loads(path.read_text())
        self.assertEqual(profile["developer_instructions"], f'# Contract\x7f\nRead [develop](<{home / ".codex-dev/skills/develop/SKILL.md"}>).\n')
        self.assertEqual(profile["agents"]["dev"]["config_file"], str(home / ".codex-dev/agents/dev.toml"))

    def test_grok_wrapper_stops_when_rules_cannot_be_read(self):
        self.run_install("--target", "grok")
        rules = self.home / ".grok-dev/AGENTS.md"
        rules.unlink()
        commands = self.base / "rule-check-commands"
        native = self.put("grok", b"#!/bin/sh\necho native-started\nexit 23\n", commands)
        native.chmod(0o755)
        result = subprocess.run([str(self.home / ".local/bin/grok-dev")], cwd=self.base,
                                env={**self.env, "HOME": str(self.home), "PATH": str(commands) + os.pathsep + self.env["PATH"]},
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(".grok-dev/AGENTS.md", result.stderr)

    def test_native_roots_must_match_install_home(self):
        for target, variable in (("codex", "CODEX_HOME"), ("grok", "GROK_HOME")):
            with self.subTest(target=target):
                outside = self.base / f"custom-{target}"
                outside.mkdir()
                before = self.snapshot(self.base)
                result = self.run_install("--target", target, env={**self.env, variable: str(outside)}, expected=1)
                self.assertIn(variable, result.stderr)
                self.assertEqual(self.snapshot(self.base), before)
                self.run_install("--target", target, env={**self.env, variable: str(self.home / f".{target}")})
                alias = self.base / f"alias-{target}"
                alias.symlink_to(self.home / f".{target}", target_is_directory=True)
                before = self.snapshot()
                self.assertIn("No managed files changed", self.run_install("--target", target, env={**self.env, variable: str(alias)}).stdout)
                self.assertEqual(self.snapshot(), before)

    def test_retired_auth_sharing_option_is_rejected_without_changes(self):
        self.put(".codex/auth.json", b"default credentials")
        self.put(".codex-dev/auth.json", b"development credentials")
        before = self.snapshot()
        result = self.run_install("--target", "codex", "--share-codex-auth", expected=2)
        self.assertIn("Unknown option", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_validates_every_target_without_changing_home(self):
        self.put(".claude/skills/old/SKILL.md", b"legacy extension\n")
        self.put(".claude.json", b'{"mcpServers": {"old": {}}, "preserved": true}')
        self.home.chmod(0o500)
        try:
            before = self.snapshot()
            result = self.run_install("--target", "all", "--clean-legacy", "--dry-run")
            self.assertIn(f"Would remove: {self.home / '.claude/skills'}", result.stdout)
            self.assertIn(f"Would write: {self.home / '.codex/dev.config.toml'}", result.stdout)
            self.assertEqual(self.snapshot(), before)
        finally:
            self.home.chmod(0o700)
        missing = self.base / "not-created"
        self.run_install("--target", "all", "--dry-run", home=missing)
        self.assertFalse(missing.exists())
        invalid = self.archive / "templates/grok/AGENTS.md"
        invalid.unlink()
        os.mkfifo(invalid)
        before = self.snapshot()
        result = self.run_install("--target", "all", "--clean-legacy", expected=1)
        self.assertIn(str(invalid), result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_cleanup_mcp_uses_isolated_native_cli_and_checks_other_settings(self):
        original = b'model = "own-model"\n[mcp_servers.old]\ncommand = "private-command"\n'
        commands = self.base / "cleanup commands"
        fake = self.put("codex", (
            f"#!{sys.executable}\nimport os, pathlib, sys\n"
            "expected = ['mcp', 'remove', '--scope', 'user', 'old'] if pathlib.Path(sys.argv[0]).name == 'grok' else ['mcp', 'remove', 'old']\n"
            "assert sys.argv[1:] == expected\n"
            "root = pathlib.Path(os.environ['CODEX_HOME'])\n"
            "assert str(root) == os.environ['HOME'] == os.getcwd()\n"
            "assert 'mcp_servers.old' in (root / 'config.toml').read_text()\n"
            "mode = os.environ['TEST_MCP_RESULT']\n"
            "if mode == 'failure':\n"
            "    print('sensitive-native-output', file=sys.stderr)\n"
            "    sys.exit(7)\n"
            "(root / 'config.toml').write_text('model = \"' + ('changed' if mode == 'tamper' else 'own-model') + '\"\\n')\n"
        ).encode(), commands)
        fake.chmod(0o755)
        shutil.copy2(fake, commands / "grok")
        for client, mode in ((client, mode) for client in ("codex", "grok") for mode in ("failure", "tamper", "success")):
            with self.subTest(client=client, mode=mode):
                home = self.base / f"mcp-{client}-{mode}"
                path = self.put(f".{client}/config.toml", original, home)
                path.chmod(0o640)
                self.put(".claude/skills/old/SKILL.md", b"legacy extension", home)
                env = {**self.env, "PATH": str(commands) + os.pathsep + self.env["PATH"], "TEST_MCP_RESULT": mode}
                before = self.snapshot(home)
                result = self.run_install("--target", "all", "--clean-legacy", home=home, env=env,
                                          expected=0 if mode == "success" else 1)
                self.assertNotIn("sensitive-native-output", result.stdout + result.stderr)
                self.assertNotIn("private-command", result.stdout + result.stderr)
                if mode != "success":
                    self.assertEqual(self.snapshot(home), before)
                    self.assertIn("exit 7" if mode == "failure" else "unrelated configuration", result.stderr)
                else:
                    self.assertEqual(tomllib.loads(path.read_text()), {"model": "own-model"})
                    self.assertEqual(path.stat().st_mode & 0o7777, 0o640)
                    backup = next((home / ".local/state/claude-dev/backups").iterdir())
                    self.assertEqual((backup / f".{client}/config.toml").read_bytes(), original)
                    before = self.snapshot(home)
                    self.run_install("--target", "all", "--clean-legacy", home=home, env={**env, "TEST_MCP_RESULT": "failure"})
                    self.assertEqual(self.snapshot(home), before)

    def test_cleanup_rejects_special_config_files_before_reading(self):
        for relative in (".claude/settings.json", ".codex/config.toml", ".grok/config.toml"):
            with self.subTest(relative=relative):
                home = self.base / (relative.split("/")[0] + "-fifo")
                path = home / relative
                path.parent.mkdir(parents=True)
                os.mkfifo(path)
                before = self.snapshot(home)
                result = subprocess.run([str(self.archive / "install.sh"), "--home", str(home),
                                         "--target", "all", "--clean-legacy"], env=self.env,
                                        capture_output=True, text=True, timeout=2)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"refusing to read non-regular {path}", result.stderr)
                self.assertEqual(self.snapshot(home), before)

    def test_home_resolution_and_argument_errors(self):
        result = subprocess.run([str(self.archive / "install.sh")], cwd=self.base,
                                env={**self.env, "HOME": str(self.home)}, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No managed files changed", self.run_install(home="~", env={**self.env, "HOME": str(self.home)}).stdout)
        self.run_install(home="~/nested", env={**self.env, "HOME": str(self.home)})
        self.assertTrue((self.home / "nested/.local/bin/claude-dev").is_file())
        self.run_install(home="relative/home")
        self.assertTrue((self.base / "relative/home/.local/bin/claude-dev").is_file())
        actual = self.base / "actual"
        (actual / "child").mkdir(parents=True)
        alias = self.base / "alias"
        alias.symlink_to(actual / "child", target_is_directory=True)
        self.run_install(home=alias / "../new/nested")
        wrapper = actual / "new/nested/.local/bin/claude-dev"
        self.assertIn(str(actual / "new/nested/.claude-dev"), wrapper.read_text())
        self.assertFalse((self.base / "new").exists())
        before = self.snapshot()
        for args, expected in ((["--help"], 0), (["-h"], 0), (["--unknown"], 2), (["--home"], 2), (["unexpected"], 2)):
            result = subprocess.run([str(self.archive / "install.sh"), *args], env=self.env,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertIn("usage:", (result.stdout + result.stderr).lower())
        self.run_install(home="~another-user", expected=1)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(Path(self.env["HOME"]).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
