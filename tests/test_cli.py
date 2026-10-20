"""Scripted Messages protocol checks, plus opt-in native Claude checks.

Run: CLAUDE_DEV_TEST_CLI=1 python3 -m unittest discover -s tests -p test_cli.py -v
These checks do not evaluate model reasoning or adherence to instructions.
"""

import gzip
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import shlex
import signal
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
READ_TOOLS = {"Read", "Grep", "Glob"}
CALL_ID = "call_review_probe"


class ModelHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.split("?", 1)[0] != "/v1/messages":
            self.send_error(404)
            return
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        body = json.loads(raw)
        self.server.requests.append(body)
        content = [{"type": "text", "text": "probe ok"}]
        stop_reason = "end_turn"
        completed = any(
            item.get("type") == "tool_result" and item.get("tool_use_id") == CALL_ID
            for message in body.get("messages", [])
            if message.get("role") == "user" and isinstance(message.get("content"), list)
            for item in message["content"]
        )
        # Retries keep the same response; the read-only worker cannot delegate.
        can_delegate = any(tool.get("name") == "Agent" for tool in body.get("tools", []))
        if self.server.delegate and can_delegate and not completed:
            content = [{"type": "tool_use", "id": CALL_ID, "name": "Agent", "input": {
                "subagent_type": "review", "description": "Probe the read-only reviewer",
                "prompt": "Return probe ok using the configured review role.",
                "run_in_background": False,
            }}]
            stop_reason = "tool_use"
        elif getattr(self.server, "tool_call", None) and not completed:
            content = [{"type": "tool_use", "id": CALL_ID, **self.server.tool_call}]
            stop_reason = "tool_use"
        response = {
            "id": f"msg_probe_{len(self.server.requests)}", "type": "message", "role": "assistant",
            "model": body["model"], "content": content,
            "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 2},
        }
        if body.get("stream"):
            block = content[0]
            if block["type"] == "tool_use":
                start = {**block, "input": {}}
                delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
            else:
                start = {"type": "text", "text": ""}
                delta = {"type": "text_delta", "text": block["text"]}
            events = [
                {"type": "message_start", "message": {
                    **response, "content": [], "stop_reason": None,
                    "usage": {"input_tokens": 1, "output_tokens": 0},
                }},
                {"type": "content_block_start", "index": 0, "content_block": start},
                {"type": "content_block_delta", "index": 0, "delta": delta},
                {"type": "content_block_stop", "index": 0},
                {"type": "message_delta", "delta": {
                    "stop_reason": stop_reason, "stop_sequence": None,
                }, "usage": {"output_tokens": 2}},
                {"type": "message_stop"},
            ]
            data = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
                           for event in events).encode()
            content_type = "text/event-stream"
        else:
            data = json.dumps(response).encode()
            content_type = "application/json"
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


class ModelHandlerTests(unittest.TestCase):
    def test_transports_and_retries_follow_conversation_state(self):
        server = SimpleNamespace(requests=[], delegate=True)
        for tools, result_id, expected in [
            (["Agent"], None, "tool_use"),
            (["Read", "Grep", "Glob"], None, "text"),
            (["Agent"], "unrelated_call", "tool_use"),
            (["Agent"], CALL_ID, "text"),
            (["Agent"], None, "tool_use"),
        ]:
            messages = [{"role": "user", "content": "probe"}]
            if result_id:
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": result_id, "content": "probe ok",
                }]})
            for stream in (False, True):
                for retry in range(2):
                    with self.subTest(tools=tools, result_id=result_id, stream=stream, retry=retry):
                        body = {"model": "claude-sonnet-4-6", "stream": stream,
                                "tools": [{"name": name} for name in tools], "messages": messages}
                        raw = json.dumps(body).encode()
                        handler = object.__new__(ModelHandler)
                        handler.server = server
                        handler.path = "/v1/messages"
                        handler.requestline = "POST /v1/messages HTTP/1.1"
                        handler.request_version = "HTTP/1.1"
                        handler.headers = {"Content-Length": str(len(raw))}
                        handler.rfile, handler.wfile = io.BytesIO(raw), io.BytesIO()
                        handler.do_POST()
                        headers, data = handler.wfile.getvalue().split(b"\r\n\r\n", 1)
                        self.assertEqual(headers.splitlines()[0].split()[1], b"200")
                        self.assertIn(f"Content-Length: {len(data)}".encode(), headers)
                        if stream:
                            self.assertIn(b"Content-Type: text/event-stream\r\n", headers + b"\r\n")
                            events = []
                            for event in data.decode().strip().split("\n\n"):
                                name, payload = event.split("\n")
                                value = json.loads(payload.removeprefix("data: "))
                                self.assertEqual(name, f"event: {value['type']}")
                                events.append(value)
                            self.assertEqual([event["type"] for event in events], [
                                "message_start", "content_block_start", "content_block_delta",
                                "content_block_stop", "message_delta", "message_stop",
                            ])
                            response = events[0]["message"]
                            self.assertEqual(response["content"], [])
                            self.assertIsNone(response["stop_reason"])
                            self.assertEqual([event["index"] for event in events[1:4]], [0, 0, 0])
                            block, delta = events[1]["content_block"], events[2]["delta"]
                            if delta["type"] == "input_json_delta":
                                self.assertEqual(block["input"], {})
                                block["input"] = json.loads(delta["partial_json"])
                            else:
                                self.assertEqual(delta["type"], "text_delta")
                                self.assertEqual(block["text"], "")
                                block["text"] += delta["text"]
                            response["content"] = [block]
                            response.update(events[4]["delta"])
                            self.assertEqual(response["content"], json_content)
                        else:
                            self.assertIn(b"Content-Type: application/json\r\n", headers + b"\r\n")
                            response = json.loads(data)
                            json_content = response["content"]
                        self.assertEqual(response["content"][0]["type"], expected)
                        self.assertEqual(response["stop_reason"], "tool_use" if expected == "tool_use" else "end_turn")
                        if expected == "tool_use":
                            self.assertEqual(response["content"][0]["id"], CALL_ID)
                            self.assertEqual(response["content"][0]["name"], "Agent")
                            self.assertEqual(response["content"][0]["input"]["subagent_type"], "review")
                        else:
                            self.assertEqual(response["content"], [{"type": "text", "text": "probe ok"}])


@unittest.skipUnless(os.environ.get("CLAUDE_DEV_TEST_CLI") == "1", "set CLAUDE_DEV_TEST_CLI=1 for native CLI checks")
class NativeCliTests(unittest.TestCase):
    def setUp(self):
        self.claude = shutil.which("claude")
        self.assertIsNotNone(self.claude, "Claude Code must be installed for the requested native checks")
        self.temp = tempfile.TemporaryDirectory(prefix="claude-dev-cli-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "runtime-home [1]*?{a,b}(x)!+@|]"
        self.home.mkdir()
        self.install_home = Path(self.temp.name) / "install-home"
        self.project = self.home / "project"
        self.project.mkdir()
        normal = self.home / ".claude"
        normal.mkdir()
        # A blocked localhost socket is a test error, not a skipped or passing check.
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
        self.server.requests = []
        self.server.delegate = False
        self.server.tool_call = None
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TERM") if key in os.environ}
        self.env.update(
            HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_CACHE_HOME=str(self.home / ".cache"), XDG_STATE_HOME=str(self.home / ".state"),
            CLAUDE_CONFIG_DIR=str(normal), ANTHROPIC_API_KEY="local-probe-key",
            ANTHROPIC_BASE_URL=f"http://127.0.0.1:{self.server.server_port}",
            CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", NO_PROXY="127.0.0.1,localhost",
        )
        result = subprocess.run(
            [str(ROOT / "install.sh"), "--home", str(self.install_home)], env=self.env,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.wrapper = str(self.install_home / ".local/bin/claude-dev")

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive(), "Local model server did not stop")

    def run_cli(self, command, *extra, delegate=False):
        self.server.requests.clear()
        self.server.delegate = delegate
        arguments = [command, "-p", "probe", "--output-format", "stream-json", "--verbose",
                     "--model", "claude-sonnet-4-6", "--max-turns", "4", "--strict-mcp-config", *extra]
        process = subprocess.Popen(
            arguments, cwd=self.project, env=self.env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=45)
        finally:
            # Also clean up descendants if the CLI exits before they do.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        self.assertEqual(process.returncode, 0, stdout + stderr)
        events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
        result = next(event for event in events if event.get("type") == "result")
        self.assertFalse(result.get("is_error"), stdout)
        if command == self.wrapper:
            initialized = next(event for event in events
                               if event.get("type") == "system" and event.get("subtype") == "init")
            self.assertEqual(initialized["permissionMode"], "bypassPermissions")
        self.assertIn("probe ok", stdout)
        self.assertTrue(self.server.requests, "CLI did not use the local model")
        return "\n".join(strings(self.server.requests))

    def assert_profile(self, prompt, loaded):
        root = (ROOT / "templates/CLAUDE.md").read_text().strip()
        paths = [ROOT / "templates/agents" / f"{role}.md"
                 for role in ("research", "arch", "dev", "simplify", "review")]
        paths.append(ROOT / "templates/skills/develop/SKILL.md")
        descriptions = [next(line.removeprefix("description: ") for line in path.read_text().splitlines()
                             if line.startswith("description: ")) for path in paths]
        for text in [root, *descriptions]:
            with self.subTest(text=text[:80], loaded=loaded):
                if loaded:
                    self.assertIn(text, prompt)
                else:
                    self.assertNotIn(text, prompt)

    def assert_role_toolset(self, role, tools, optional_tools=frozenset()):
        body = (ROOT / "templates/agents" / f"{role}.md").read_text().split("---", 2)[2].strip()
        requests = [request for request in self.server.requests
                    if body in "\n".join(strings(request.get("system", [])))]
        self.assertTrue(requests, f"No request loaded the actual {role} role body")
        for request in requests:
            actual = {tool["name"] for tool in request.get("tools", [])}
            self.assertTrue(tools <= actual, f"Missing {role} tools: {tools - actual}")
            self.assertTrue(actual <= tools | optional_tools,
                            f"Unexpected {role} tools: {actual - tools - optional_tools}")

    def assert_instruction_isolation(self, filename):
        default_markers = {filename: "DEFAULT_ROOT_PROBE", "rules/probe.md": "DEFAULT_RULE_PROBE"}
        project_markers = {filename: "PROJECT_ROOT_PROBE", ".claude/rules/probe.md": "PROJECT_RULE_PROBE"}
        # Keep CLAUDE and AGENTS in separate fixtures so fallback remains observable.
        for directory, markers in ((self.home / ".claude", default_markers), (self.project, project_markers)):
            for relative, marker in markers.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{marker}\n")
        normal = self.run_cli(self.claude)
        development = self.run_cli(self.wrapper)
        for marker in default_markers.values():
            self.assertIn(marker, normal)
            self.assertNotIn(marker, development)
        for marker in project_markers.values():
            self.assertIn(marker, normal)
            self.assertIn(marker, development)
        self.assert_profile(normal, False)
        self.assert_profile(development, True)

    def test_default_claude_isolation_preserves_project_instructions(self):
        self.assert_instruction_isolation("CLAUDE.md")

    def test_default_agents_fallback_isolation_preserves_project_instructions(self):
        self.assert_instruction_isolation("AGENTS.md")

    def test_direct_review_has_only_read_tools(self):
        self.run_cli(self.wrapper, "--agent", "review")
        self.assert_role_toolset("review", READ_TOOLS)

    def test_direct_research_has_only_read_and_web_tools(self):
        self.run_cli(self.wrapper, "--agent", "research")
        self.assert_role_toolset("research", READ_TOOLS | {"WebSearch", "WebFetch"})

    def test_direct_simplify_can_edit_project(self):
        destination = self.project / "simplified.txt"
        self.server.tool_call = {"name": "Write", "input": {
            "file_path": str(destination), "content": "probe ok\n",
        }}
        self.run_cli(self.wrapper, "--agent", "simplify")
        # 2.1.302 omits Grep/Glob from writable dev and simplify requests.
        self.assert_role_toolset("simplify", {"Read", "Edit", "Write", "Bash"}, {"Grep", "Glob"})
        self.assertEqual(destination.read_text(), "probe ok\n")
        results = [item for request in self.server.requests for message in request.get("messages", [])
                   if isinstance(message.get("content"), list) for item in message["content"]
                   if item.get("type") == "tool_result" and item.get("tool_use_id") == CALL_ID]
        self.assertTrue(results, "The simplify write result did not reach the local model")
        self.assertTrue(all(not item.get("is_error") for item in results), results)

    def test_wrapper_disables_approval_and_bash_sandbox(self):
        destination = Path(self.temp.name) / "outside-project.txt"
        settings = self.install_home / ".claude-dev/settings.json"
        original = json.loads(settings.read_text())
        settings.write_text(json.dumps({**original, "permissions": {"defaultMode": "acceptEdits"},
                                       "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": False,
                                                   "filesystem": {"denyWrite": [str(destination)]}}}))
        self.server.tool_call = {"name": "Bash", "input": {
            "command": f"printf 'probe ok' > {shlex.quote(str(destination))}",
            "description": "Write the disposable permissions probe outside the project",
        }}
        self.run_cli(self.wrapper)
        self.assertEqual(destination.read_text(), "probe ok")
        results = [item for request in self.server.requests for message in request.get("messages", [])
                   if isinstance(message.get("content"), list) for item in message["content"]
                   if item.get("type") == "tool_result" and item.get("tool_use_id") == CALL_ID]
        self.assertTrue(results, "The shell tool result did not reach the local model")
        self.assertTrue(all(not item.get("is_error") for item in results), results)

    def test_named_review_subagent_has_only_read_tools(self):
        self.run_cli(self.wrapper, delegate=True)
        self.assertIn("Agent", {tool["name"] for tool in self.server.requests[0].get("tools", [])})
        self.assertGreaterEqual(len(self.server.requests), 3, "Expected main, review worker, resumed main requests")
        self.assert_role_toolset("review", READ_TOOLS)
        results = []
        for request in self.server.requests:
            for message in request.get("messages", []):
                content = message.get("content")
                if isinstance(content, list):
                    results.extend(item for item in content
                                   if item.get("type") == "tool_result" and item.get("tool_use_id") == CALL_ID)
        self.assertTrue(results, "Main session did not receive the named worker's result")
        self.assertTrue(all(not item.get("is_error") for item in results), results)


if __name__ == "__main__":
    unittest.main()
