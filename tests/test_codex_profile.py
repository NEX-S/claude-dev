"""Validate installed Codex overlays without starting a model turn.

Native prompt inspection proves root loading, not child behavior or isolation.
Codex 0.157.1 applies only bounded role overrides and inherits parent permissions.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "codex"
CODEX = shutil.which("codex")


class CodexProfileTests(unittest.TestCase):
    def test_roles_use_supported_overrides_and_preserve_model_inheritance(self):
        config = tomllib.loads((TEMPLATES / "config.toml").read_text())
        self.assertEqual(set(config), {"agents"})
        self.assertEqual(set(config["agents"]), {"research", "arch", "dev", "simplify", "review"})
        self.assertEqual({path.stem for path in (TEMPLATES / "agents").glob("*.toml")},
                         set(config["agents"]))
        shared_contracts = []
        for name, registration in config["agents"].items():
            with self.subTest(role=name):
                path = (TEMPLATES / registration["config_file"]).resolve()
                self.assertTrue(path.is_relative_to(TEMPLATES.resolve()))
                role = tomllib.loads(path.read_text())
                # 0.157.1 core/src/agent/role.rs filters sandbox_mode,
                # approval_policy, agents.enabled, and features.multi_agent.
                # These files deliberately supply instructions, not false isolation.
                self.assertEqual(set(role), {"name", "description", "developer_instructions"})
                self.assertEqual(role["name"], name)
                self.assertEqual(role["description"], registration["description"])
                self.assertTrue(role["developer_instructions"].strip())
                shared_contracts.append(role["developer_instructions"].strip().split("\n\n", 1)[0])
                self.assertNotIn("model", role)
                self.assertNotIn("model_reasoning_effort", role)
        # Named roles replace the parent's developer instructions, so each needs this contract.
        self.assertTrue(shared_contracts[0])
        self.assertEqual(len(set(shared_contracts)), 1)

    @unittest.skipUnless(CODEX and shutil.which("bun"), "Codex CLI and Bun are required")
    def test_installed_native_overlay_preserves_base_configuration(self):
        with tempfile.TemporaryDirectory(prefix="codex-overlay-test-") as directory:
            root = Path(directory)
            home, project = root / "home with (spaces)", root / "project"
            native = home / ".codex"
            native.mkdir(parents=True)
            project.mkdir()
            (project / ".git").mkdir()
            (project / "AGENTS.md").write_text("PROJECT_INSTRUCTIONS_MARKER\n")
            (native / "AGENTS.md").write_text("DEFAULT_INSTRUCTIONS_MARKER\n")
            (native / "AGENTS.override.md").write_text("DEFAULT_OVERRIDE_MARKER\n")
            base = native / "config.toml"
            base.write_text(
                'developer_instructions = "BASE_DEVELOPER_MARKER"\n'
                'model = "base-model-marker"\n'
                'model_provider = "base-provider"\n'
                'model_reasoning_effort = "high"\n'
                'sandbox_mode = "read-only"\n'
                'approval_policy = "on-request"\n'
                'cli_auth_credentials_store = "file"\n'
                '[model_providers.base-provider]\n'
                'name = "Base provider"\n'
                'base_url = "http://127.0.0.1:1/v1"\n'
                'wire_api = "responses"\n'
                'requires_openai_auth = false\n'
            )
            auth = native / "auth.json"
            auth.write_text(json.dumps({"auth_mode": "apikey", "OPENAI_API_KEY": "sk-local-overlay-test"}))
            history = native / "history.jsonl"
            history.write_text("{\"probe\":\"preserve history\"}\n")
            preserved = {path: path.read_bytes() for path in (base, auth, history)}
            env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_DATA_HOME": str(root / "data"),
                "LANG": "C.UTF-8",
            }

            def run(*args, expected=0):
                result = subprocess.run(args, cwd=project, env=env, capture_output=True,
                                        text=True, timeout=20)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return result

            run(str(ROOT / "install.sh"), "--home", str(home), "--target", "codex")
            wrapper = str(home / ".local/bin/codex-dev")
            profile = native / "dev.config.toml"
            installed = tomllib.loads(profile.read_text())
            self.assertEqual(set(installed), {"developer_instructions", "agents"})
            workflow = home / ".codex-dev/skills/develop/SKILL.md"
            expected_root = (TEMPLATES / "AGENTS.md").read_text().replace(
                "skills/develop/SKILL.md", f"<{workflow}>")
            self.assertEqual(installed["developer_instructions"], expected_root)
            expected_agents = tomllib.loads((TEMPLATES / "config.toml").read_text())["agents"]
            for name, registration in expected_agents.items():
                self.assertEqual(installed["agents"][name], {
                    **registration,
                    "config_file": str(home / ".codex-dev" / registration["config_file"]),
                })
                self.assertEqual(Path(installed["agents"][name]["config_file"]).read_bytes(),
                                 (TEMPLATES / registration["config_file"]).read_bytes())
            self.assertEqual(workflow.read_bytes(), (TEMPLATES / "skills/develop/SKILL.md").read_bytes())

            for command, development in ((CODEX, False), (wrapper, True)):
                with self.subTest(command=command):
                    result = run(command, "--no-daemon", "debug", "prompt-input")
                    text = "\n".join(part.get("text", "") for item in json.loads(result.stdout)
                                     for part in item.get("content", []))
                    self.assertIn("PROJECT_INSTRUCTIONS_MARKER", text)
                    self.assertIn("DEFAULT_OVERRIDE_MARKER", text)
                    self.assertNotIn("DEFAULT_INSTRUCTIONS_MARKER", text)
                    self.assertEqual(expected_root.strip() in text, development)
                    self.assertEqual("BASE_DEVELOPER_MARKER" in text, not development)
                    self.assertEqual(str(workflow) in text, development)
                    self.assertNotIn(workflow.read_text().split("---", 2)[2].strip(), text)
                    description = workflow.read_text().split("description: ", 1)[1].splitlines()[0]
                    self.assertNotIn(description, text)
                    permissions = next(part["text"] for item in json.loads(result.stdout)
                                       for part in item.get("content", [])
                                       if part.get("text", "").startswith("<permissions instructions>"))
                    self.assertIn('`sandbox_mode` is `danger-full-access`' if development else
                                  '`sandbox_mode` is `read-only`', permissions)
                    self.assertEqual("Approval policy is currently never" in permissions, development)

            # Wrong base values must remain visible to native validation through the overlay.
            for field, replacement in (("model", 'model = 123'),
                                       ("model_provider", 'model_provider = "missing-provider-marker"')):
                with self.subTest(base_field=field):
                    original = preserved[base].decode()
                    line = next(line for line in original.splitlines() if line.startswith(field + " ="))
                    base.write_text(original.replace(line, replacement))
                    rejected = run(wrapper, "--no-daemon", "debug", "prompt-input", expected=1)
                    self.assertIn("string" if field == "model" else "missing-provider-marker", rejected.stderr)
                    base.write_bytes(preserved[base])

            for path, original in preserved.items():
                self.assertEqual(path.read_bytes(), original, str(path))
            self.assertFalse((home / ".codex-dev/auth.json").exists())
            # Profile flags are intentionally unsupported by Codex's account-management commands.
            rejected = run(wrapper, "login", "status", expected=1)
            self.assertIn("--profile only applies", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
