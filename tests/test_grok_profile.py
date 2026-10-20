"""Validate Grok's installed overlay without real credentials or model turns.

Set GROK_BIN to an installed Grok executable when it is not on PATH.
Inspect proves discovery, not final prompt injection or runtime tool permissions.
The offline startup checks use fake cached auth in an isolated network namespace;
they prove local startup and effective settings, not model or tool execution.
"""

import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import subprocess
import tempfile
import termios
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "templates/grok"
GROK = os.environ.get("GROK_BIN") or shutil.which("grok")


class GrokProfileTests(unittest.TestCase):
    def test_read_only_roles_exclude_execution_and_mcp(self):
        for role, expected_tools in (
            ("research", {"read_file", "grep", "list_dir", "web_search", "web_fetch"}),
            ("arch", {"read_file", "grep", "list_dir", "web_search", "web_fetch"}),
            ("review", {"read_file", "grep", "list_dir"}),
        ):
            with self.subTest(role=role):
                header = (PROFILE / "agents" / f"{role}.md").read_text().split("---", 2)[1]
                fields = dict(line.split(": ", 1) for line in header.strip().splitlines())
                self.assertEqual(fields["name"], role)
                self.assertEqual(set(fields["tools"].split(", ")), expected_tools)
                self.assertEqual(json.loads(fields["disallowedTools"]), ["search_tool", "use_tool"])
                self.assertEqual(fields["mcpInheritance"], "none")
                self.assertNotIn("model", fields)
                self.assertNotIn("permissionMode", fields)

    def test_writing_roles_inherit_native_tools_and_runtime_settings(self):
        for role in ("dev", "simplify"):
            with self.subTest(role=role):
                header = (PROFILE / "agents" / f"{role}.md").read_text().split("---", 2)[1]
                fields = dict(line.split(": ", 1) for line in header.strip().splitlines())
                self.assertEqual(set(fields), {"name", "description"})
                self.assertEqual(fields["name"], role)


@unittest.skipUnless(GROK and shutil.which("git") and shutil.which("bun"),
                     "Grok, git, and Bun are required for the installed overlay")
class NativeGrokOverlayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="grok-overlay-test-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.home = root / "home (development)"
        self.default = self.home / ".grok"
        self.default.mkdir(parents=True)
        (self.default / "AGENTS.md").write_text("DEFAULT_GROK_RULE\n")
        config = self.default / "config.toml"
        # Avoid Grok's first-run migration changing the startup comparison fixture.
        config.write_text('[cli]\nuse_leader = false\n[features]\ntelemetry = false\n'
                          '[marketplace]\ndefault_skills_installs_purged = true\n')
        auth = self.default / "auth.json"
        # Native GrokAuth schema; the token is deliberately unusable at any server.
        auth.write_text(json.dumps({"https://accounts.x.ai/sign-in": {
            "key": "fixture-not-a-real-token", "auth_mode": "oidc",
            "create_time": "2026-01-01T00:00:00Z", "expires_at": "2099-01-01T00:00:00Z",
            "user_id": "fixture", "oidc_issuer": "https://auth.x.ai",
        }}) + "\n")
        agents = self.default / "agents"
        agents.mkdir()
        existing = agents / "existing.md"
        existing.write_text('---\nname: existing\ndescription: Existing user agent.\n---\nKeep this agent.\n')
        self.preserved = {path: path.read_bytes() for path in (config, auth, existing)}
        self.profile = self.home / ".grok-dev"
        commands = root / "bin"
        commands.mkdir()
        (commands / "grok").symlink_to(Path(GROK).resolve())
        self.project = self.home / "project"
        self.project.mkdir()
        self.env = {
            "PATH": str(commands) + os.pathsep + os.environ.get("PATH", ""),
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"), "TERM": "xterm-256color",
            "LANG": "C.UTF-8",
        }
        installed = subprocess.run(
            [str(ROOT / "install.sh"), "--target", "grok", "--home", str(self.home)],
            cwd=self.project, env=self.env, text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.wrapper = self.home / ".local/bin/grok-dev"
        subprocess.run(["git", "init", "-q", str(self.project)], env=self.env,
                       check=True, capture_output=True, timeout=10)
        (self.project / "AGENTS.md").write_text("PROJECT_AGENT_RULE\n")
        rules = self.project / ".claude/rules"
        rules.mkdir(parents=True)
        (rules / "project.md").write_text("PROJECT_CLAUDE_RULE\n")

    def assert_default_state_preserved(self):
        for path, original in self.preserved.items():
            self.assertEqual(path.read_bytes(), original, str(path))

    def test_installed_overlay_discovery_preserves_default_state_and_project_rules(self):
        workflow = self.profile / "skills/develop/SKILL.md"
        self.assertTrue(workflow.is_file())
        self.assertIn(f"(<{workflow}>)", (self.profile / "AGENTS.md").read_text())
        self.assertFalse((self.profile / "auth.json").exists())
        self.assertFalse((self.profile / "config.toml").exists())
        sources = []
        for command in (GROK, self.wrapper):
            with self.subTest(entry=str(command)):
                result = subprocess.run(
                    [str(command), "--trust", "inspect", "--json"], cwd=self.project,
                    env=self.env, text=True, capture_output=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                discovered = json.loads(result.stdout)
                sources.append(discovered["configSources"])
                self.assertIn(str(self.default / "config.toml"), json.dumps(sources[-1]))
                self.assertTrue(discovered["projectTrusted"])
                self.assertEqual({item["path"] for item in discovered["projectInstructions"]}, {
                    str(self.default / "AGENTS.md"), str(self.project / "AGENTS.md"),
                    str(self.project / ".claude/rules/project.md"),
                })
                definitions = {item["name"]: item for item in discovered["agents"]}
                for role in ("research", "arch", "dev", "simplify", "review", "existing"):
                    self.assertEqual(definitions[role]["source"]["path"],
                                     str(self.default / "agents" / f"{role}.md"))
                self.assertNotIn("develop", {item["name"] for item in discovered["skills"]})
                self.assertEqual(discovered["mcpServers"], [])
        self.assertEqual(sources[0], sources[1])
        self.assert_default_state_preserved()

    def test_duplicate_permission_arguments_keep_native_errors(self):
        for flag, value in (("--permission-mode", "bypassPermissions"), ("--sandbox", "off")):
            with self.subTest(flag=flag):
                result = subprocess.run([str(self.wrapper), flag, value, "inspect", "--json"],
                    cwd=self.project, env=self.env, text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("cannot be used multiple times", result.stderr)
                self.assertIn(flag, result.stderr)

    @unittest.skipUnless(shutil.which("unshare"), "unshare is required for offline startup")
    def test_wrapper_starts_with_highest_permissions_and_sandbox_off(self):
        isolated = ["unshare", "--user", "--map-root-user", "--net"]
        probe = subprocess.run([*isolated, "true"], env=self.env,
                               capture_output=True, text=True, timeout=10)
        if probe.returncode:
            self.skipTest("network namespaces unavailable: " + probe.stderr.strip())
        config = self.default / "config.toml"
        config.write_text(config.read_text() + '\n[ui]\npermission_mode = "ask"\n'
                          '[sandbox]\nprofile = "read-only"\n')
        self.preserved[config] = config.read_bytes()
        debug = self.home / "startup.log"
        process = subprocess.Popen(
            [*isolated, str(self.wrapper), "--debug-file", str(debug), "--disable-web-search",
             "--model", "grok-4.5", "--reasoning-effort", "low", "--max-turns", "1", "-p", "probe"],
            cwd=self.project, env={**self.env, "GROK_SANDBOX": "missing-permission-probe-profile"},
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and process.poll() is None:
                if debug.is_file() and "yolo_mode changed via before-turn hook" in debug.read_text():
                    break
                time.sleep(.05)
        finally:
            # The network is isolated; only startup is under test. Do not await a model response.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate(timeout=5)
        self.assertTrue(debug.is_file(), stdout + stderr)
        self.assertRegex(debug.read_text(), r"yolo_mode changed via before-turn hook[^\n]*from=false to=true")
        summaries = list((self.default / "sessions").rglob("summary.json"))
        self.assertEqual(len(summaries), 1, stdout + stderr)
        summary = json.loads(summaries[0].read_text())
        self.assertEqual(summary["sandbox_profile"], "off")
        self.assertEqual(summary["current_model_id"], "grok-4.5")
        self.assertEqual(summary["reasoning_effort"], "low")
        self.assert_default_state_preserved()

    @unittest.skipUnless(shutil.which("unshare"), "unshare is required for offline startup")
    def test_native_startup_reuses_cached_auth_offline(self):
        isolated = ["unshare", "--user", "--map-root-user", "--net"]
        probe = subprocess.run([*isolated, "true"], env=self.env,
                               capture_output=True, text=True, timeout=10)
        if probe.returncode:
            self.skipTest("network namespaces unavailable: " + probe.stderr.strip())
        login_request = "auth: authenticate request method=grok.com"
        for index, (command, env, cached_auth) in enumerate((
            (GROK, self.env, True),
            (self.wrapper, self.env, True),
            (GROK, {**self.env, "GROK_HOME": str(self.profile)}, False),
        )):
            with self.subTest(entry=str(command), grok_home=env.get("GROK_HOME")):
                master, slave = pty.openpty()
                process = None
                output = bytearray()
                debug = self.home / f"auth-startup-{index}.log"
                try:
                    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 160, 0, 0))
                    process = subprocess.Popen(
                        [*isolated, str(command), "--debug-file", str(debug), "--trust", "--no-alt-screen"],
                        cwd=self.project,
                        env=env, stdin=slave, stdout=slave, stderr=slave,
                        start_new_session=True,
                        preexec_fn=lambda: fcntl.ioctl(slave, termios.TIOCSCTTY, 0),
                    )
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline and process.poll() is None:
                        if not select.select([master], [], [], min(.25, max(0, deadline - time.monotonic())))[0]:
                            continue
                        try:
                            chunk = os.read(master, 65536)
                        except OSError as error:
                            if error.errno == errno.EIO:
                                break
                            raise
                        if not chunk:
                            break
                        output.extend(chunk)
                        if b"\x1b[6n" in chunk:
                            os.write(master, b"\x1b[1;1R")
                        if cached_auth and b"Resume session" in output:
                            break
                        if not cached_auth and debug.is_file() and login_request in debug.read_text():
                            break
                finally:
                    if process is not None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait(timeout=5)
                    os.close(master)
                    os.close(slave)
                diagnostics = debug.read_text() if debug.is_file() else ""
                if cached_auth:
                    self.assertIn(b"Resume session", output, output[-1500:].decode(errors="replace"))
                    self.assertFalse(b"Login with Grok" in output)
                    self.assertNotIn("auto-triggering login at startup", diagnostics)
                else:
                    # 1.0.52 starts native login immediately; offline OIDC discovery
                    # leaves the UI at Connecting rather than showing a login button.
                    self.assertIn("auto-triggering login at startup", diagnostics)
                    self.assertIn(login_request, diagnostics)
                    self.assertNotIn(b"Resume session", output)
        self.assertFalse((self.profile / "auth.json").exists())
        self.assert_default_state_preserved()


if __name__ == "__main__":
    unittest.main()
