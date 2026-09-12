"""Opt-in native CLI loading checks, served entirely by a local fake model.

Run: CLAUDEX_TEST_CLI=1 python3 -m unittest discover -s tests -p test_cli.py -v
"""

import gzip
import http.server
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ModelHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        body = json.loads(raw)
        self.server.requests.append(body)
        if self.path.startswith("/v1/messages"):
            response = {
                "id": "msg_probe", "type": "message", "role": "assistant",
                "model": "claude-sonnet-4-6",
                "content": [{"type": "text", "text": "probe ok"}],
                "stop_reason": "end_turn", "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 2},
            }
            data = json.dumps(response).encode()
            content_type = "application/json"
        elif self.path == "/v1/responses":
            item = {
                "id": "msg_probe", "type": "message", "role": "assistant",
                "content": [{"type": "output_text", "text": "probe ok", "annotations": []}],
                "status": "completed",
            }
            events = [
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {"type": "response.completed", "response": {
                    "id": "resp_probe", "object": "response", "status": "completed",
                    "output": [item],
                    "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
                }},
            ]
            data = "".join(f"data: {json.dumps(event)}\n\n" for event in events).encode()
            content_type = "text/event-stream"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


@unittest.skipUnless(os.environ.get("CLAUDEX_TEST_CLI") == "1", "set CLAUDEX_TEST_CLI=1 for native CLI checks")
class NativeCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claudex-cli-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.project = self.home / "project"
        self.project.mkdir()
        result = subprocess.run(
            [str(ROOT / "install.sh"), "--home", str(self.home)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("ANTHROPIC", "CLAUDE", "CODEX", "OPENAI"))
        }
        # Native CLIs also discover user files outside their configuration roots.
        self.env["HOME"] = str(self.home)
        self.env["NO_PROXY"] = "127.0.0.1,localhost"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_cli(self, command):
        self.server.requests.clear()
        process = subprocess.Popen(
            command, cwd=self.project, env=self.env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            # Codex's Node launcher owns a native child; kill the whole test session.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise
        self.assertEqual(process.returncode, 0, stdout + stderr)
        self.assertIn("probe ok", stdout)
        self.assertTrue(self.server.requests, "CLI did not use the local model")
        return "\n".join(strings(self.server.requests))

    def assert_scaffolding(self, prompt, loaded):
        root = (ROOT / "templates/AGENTS.md").read_text().strip()
        roles = sorted((ROOT / "templates/agents").glob("*.md"))
        skills = sorted((ROOT / "templates/skills").glob("*/SKILL.md"))
        self.assertEqual({path.stem for path in roles}, {"arch", "dev", "plan", "refine", "research", "review"})
        self.assertEqual({path.parent.name for path in skills}, {"orchestrate", "author-skills"})
        descriptions = []
        for path in [*roles, *skills]:
            description = next(line.removeprefix("description: ") for line in path.read_text().splitlines()
                               if line.startswith("description: "))
            descriptions.append((str(path.relative_to(ROOT)), description))
        for label, text in [("root instructions", root), *descriptions]:
            with self.subTest(artifact=label, loaded=loaded):
                if loaded:
                    self.assertIn(text, prompt)
                else:
                    self.assertNotIn(text, prompt)

    @unittest.skipUnless(shutil.which("claude"), "Claude Code is not installed")
    def test_claude_native_and_dev_loading(self):
        normal = self.home / ".claude"
        normal.mkdir(exist_ok=True)
        self.env.update(
            CLAUDE_CONFIG_DIR=str(normal), ANTHROPIC_API_KEY="local-probe-key",
            ANTHROPIC_BASE_URL=self.url, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
        )
        args = ["-p", "probe", "--output-format", "json", "--model", "claude-sonnet-4-6",
                "--max-turns", "1", "--strict-mcp-config"]
        self.assert_scaffolding(self.run_cli(["claude", *args]), False)
        self.assert_scaffolding(self.run_cli([str(self.home / ".local/bin/claude-dev"), *args]), True)

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_codex_native_and_dev_loading(self):
        normal = self.home / ".codex"
        normal.mkdir(exist_ok=True)
        config = (
            'model="probe"\nmodel_provider="probe"\nweb_search="disabled"\n'
            '[features]\nenable_request_compression=false\n'
            '[model_providers.probe]\nname="Probe"\n'
            f'base_url="{self.url}/v1"\nwire_api="responses"\nrequest_max_retries=0\n'
        )
        for path in (normal, self.home / ".codex-dev"):
            (path / "config.toml").write_text(config)
        self.env["CODEX_HOME"] = str(normal)
        args = ["exec", "--skip-git-repo-check", "probe"]
        self.assert_scaffolding(self.run_cli(["codex", *args]), False)
        self.assert_scaffolding(self.run_cli([str(self.home / ".local/bin/codex-dev"), *args]), True)


if __name__ == "__main__":
    unittest.main()
