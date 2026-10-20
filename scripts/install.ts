#!/usr/bin/env bun
import * as fs from "node:fs";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { homedir, tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, relative } from "node:path";
import { isDeepStrictEqual, parseArgs } from "node:util";

const ROOT = dirname(import.meta.dir);
type Resource = { mode: number; data: Buffer | Map<string, Resource> };

function readResource(path: string): Resource {
  const status = fs.lstatSync(path);
  const mode = status.mode & 0o7777;
  if (status.isFile()) return { mode, data: fs.readFileSync(path) };
  if (status.isDirectory()) {
    return { mode, data: new Map(fs.readdirSync(path).sort().map(name => [name, readResource(join(path, name))])) };
  }
  throw new Error(`source must be a regular file or directory: ${path}`);
}

function matches(path: string, resource: Resource): boolean {
  const status = fs.lstatSync(path, { throwIfNoEntry: false });
  if (!status || (status.mode & 0o7777) !== resource.mode) return false;
  if (Buffer.isBuffer(resource.data)) return status.isFile() && fs.readFileSync(path).equals(resource.data);
  if (!status.isDirectory()) return false;
  const children = resource.data;
  const names = fs.readdirSync(path);
  return names.length === children.size && names.every(name => children.has(name) && matches(join(path, name), children.get(name)!));
}

function writeResource(path: string, resource: Resource) {
  if (Buffer.isBuffer(resource.data)) fs.writeFileSync(path, resource.data, { flag: "wx", mode: 0o600 });
  else {
    fs.mkdirSync(path, { mode: 0o700 });
    for (const [name, child] of resource.data) writeResource(join(path, name), child);
  }
  fs.chmodSync(path, resource.mode);
}

function checkDirectory(home: string, path: string) {
  if (path !== home) checkDirectory(home, dirname(path));
  const status = fs.lstatSync(path, { throwIfNoEntry: false });
  if (status && !status.isDirectory()) throw new Error(`refusing parent that is a symlink or non-directory: ${path}`);
}

function checkWritable(path: string) {
  while (!fs.lstatSync(path, { throwIfNoEntry: false })) path = dirname(path);
  fs.accessSync(path, fs.constants.W_OK | fs.constants.X_OK);
}

// Follow links before applying ..; Bun realpath normalizes .. too early.
// A missing suffix is valid when installing into a new directory.
function canonicalPath(path: string, activeLinks = new Set<string>()): string {
  let resolved = "/";
  for (const part of path.split("/")) {
    if (!part || part === ".") continue;
    if (part === "..") {
      resolved = dirname(resolved);
      continue;
    }
    const next = join(resolved, part);
    const status = fs.lstatSync(next, { throwIfNoEntry: false });
    if (status?.isSymbolicLink()) {
      if (activeLinks.has(next)) throw new Error(`symbolic link loop: ${next}`);
      activeLinks.add(next);
      const target = fs.readlinkSync(next);
      resolved = canonicalPath(isAbsolute(target) ? target : `${resolved}/${target}`, activeLinks);
      activeLinks.delete(next);
    } else {
      if (status && !status.isDirectory()) throw new Error(`--home: not a directory: ${next}`);
      resolved = next;
    }
  }
  return resolved;
}

function readConfiguration(path: string, format: "JSON" | "TOML") {
  const status = fs.lstatSync(path, { throwIfNoEntry: false });
  if (!status) return;
  const targetStatus = status.isSymbolicLink() ? fs.statSync(path) : status;
  if (!targetStatus.isFile()) throw new Error(`refusing to read non-regular ${path}`);
  const data = fs.readFileSync(path);
  let value: unknown;
  try {
    value = format === "JSON" ? JSON.parse(data.toString()) : Bun.TOML.parse(data.toString());
  } catch {
    // Parser diagnostics can include credentials from the invalid source line.
    throw new Error(`cannot parse ${path}: invalid ${format}`);
  }
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`expected a ${format} object: ${path}`);
  return { status, data, value: value as Record<string, unknown> };
}

function tomlString(value: string): string {
  // TOML basic strings also require DEL to be escaped; JSON leaves it literal.
  return JSON.stringify(value).replaceAll("\x7f", "\\u007f");
}

async function install(home: string, target: string, cleanLegacy: boolean, dryRun: boolean) {
  const targets = target === "all" ? ["claude", "codex", "grok"] : [target];
  // An absent resource means move the old path into the backup without replacing it.
  const artifacts = new Map<string, Resource | undefined>();
  for (const client of targets) {
    if (client !== "claude") {
      const variable = client === "codex" ? "CODEX_HOME" : "GROK_HOME";
      const configured = process.env[variable];
      const expected = join(home, `.${client}`);
      if (configured && canonicalPath(isAbsolute(configured) ? configured : `${process.cwd()}/${configured}`) !== canonicalPath(expected)) {
        throw new Error(`${variable} must match the installation home's standard directory: ${expected}`);
      }
    }
    const templates = join(ROOT, "templates", client === "claude" ? "" : client);
    if (!fs.lstatSync(templates).isDirectory()) throw new Error(`source must be a directory: ${templates}`);
    const profile = join(home, `.${client}-dev`);
    const names = client === "claude" ? ["CLAUDE.md", "agents", "skills"]
      : client === "codex" ? ["AGENTS.md", "config.toml", "agents", "skills"] : ["AGENTS.md", "agents", "skills"];
    for (const name of names) {
      const source = join(templates, name);
      const resource = readResource(source);
      if (Buffer.isBuffer(resource.data) !== name.includes(".")) throw new Error(`unexpected source type: ${source}`);
      if (name === "AGENTS.md") {
        resource.data = Buffer.from(resource.data.toString().replaceAll("skills/develop/SKILL.md", `<${join(profile, "skills/develop/SKILL.md")}>`));
      }
      if (client === "codex" && name === "config.toml") {
        const destination = join(home, ".codex/dev.config.toml");
        const existing = readConfiguration(destination, "TOML")?.value;
        let choices = "";
        for (const key of ["model", "model_reasoning_effort"]) {
          const value = existing?.[key];
          if (typeof value === "string") choices += `${key} = ${tomlString(value)}\n`;
        }
        const rules = artifacts.get(join(profile, "AGENTS.md"))!.data.toString();
        const skeleton = resource.data.toString().replace(/^config_file\s*=\s*"([^"\r\n]+)"[ \t]*$/gm,
          (_line, path) => `config_file = ${tomlString(join(profile, path))}`);
        const data = Buffer.from(`${choices}developer_instructions = ${tomlString(rules)}\n\n${skeleton}`);
        const parsed = Bun.TOML.parse(data.toString());
        if (!parsed.agents || typeof parsed.agents !== "object" || Array.isArray(parsed.agents)) throw new Error(`expected agent registrations: ${source}`);
        for (const [agent, registration] of Object.entries(parsed.agents)) {
          if (!registration || typeof registration !== "object" || !("config_file" in registration)
              || registration.config_file !== join(profile, "agents", `${agent}.toml`)) {
            throw new Error(`expected native agent config_file path: ${source}`);
          }
        }
        artifacts.set(destination, { mode: resource.mode, data });
      } else if (client === "codex" && name === "skills") {
        for (const [child, skill] of resource.data as Map<string, Resource>) {
          if (child === ".system") throw new Error(`native system skills cannot be managed: ${source}`);
          artifacts.set(join(profile, name, child), skill);
        }
      } else if (client === "grok" && name === "agents") {
        for (const [child, agent] of resource.data as Map<string, Resource>) {
          if (!Buffer.isBuffer(agent.data)) throw new Error(`expected an agent file: ${join(source, child)}`);
          artifacts.set(join(home, ".grok/agents", child), agent);
        }
      } else artifacts.set(join(profile, name), resource);
    }
    const wrapper = client === "claude"
      ? `#!/bin/sh\nexport CLAUDE_CONFIG_DIR='${profile.replaceAll("'", "'\"'\"'")}'\nexec claude --permission-mode bypassPermissions --settings '{"sandbox":{"enabled":false}}' "$@"\n`
      : client === "codex" ? '#!/bin/sh\nexec codex --profile dev --dangerously-bypass-approvals-and-sandbox "$@"\n'
      : `#!/bin/sh\nset -eu\nrules=$(cat '${join(profile, "AGENTS.md").replaceAll("'", "'\"'\"'")}')\nexec grok --rules "$rules" --permission-mode bypassPermissions --sandbox off "$@"\n`;
    artifacts.set(join(home, `.local/bin/${client}-dev`), {
      mode: 0o755, data: Buffer.from(wrapper),
    });
  }
  for (const path of artifacts.keys()) checkDirectory(home, dirname(path));

  if (targets.includes("claude")) {
    // Claude also loads the process user's .claude as ancestor project memory.
    const runtimeHome = canonicalPath(homedir());
    if (runtimeHome.includes("\\")) throw new Error(`cannot exclude default profile: HOME contains a backslash: ${runtimeHome}`);
    const defaultProfile = join(runtimeHome.replace(/[*?[\]{}()!+@|]/g, character => `[${character}]`), ".claude/**");
    const path = join(home, ".claude-dev/settings.json");
    const previous = readConfiguration(path, "JSON");
    const settings = previous?.value ?? {};
    const excludes = "claudeMdExcludes" in settings ? settings.claudeMdExcludes : [];
    if (!Array.isArray(excludes) || !excludes.every(value => typeof value === "string")) {
      throw new Error(`expected claudeMdExcludes to be a string array: ${path}`);
    }
    if (!excludes.includes(defaultProfile)) {
      if (previous && !previous.status.isFile()) {
        throw new Error(`refusing to replace non-regular ${path}; add ${JSON.stringify(defaultProfile)} to its claudeMdExcludes`);
      }
      artifacts.set(path, {
        mode: previous ? previous.status.mode & 0o7777 : 0o600,
        data: Buffer.from(`${JSON.stringify({ ...settings, claudeMdExcludes: [...excludes, defaultProfile] }, null, 2)}\n`),
      });
    }
  }

  if (cleanLegacy) {
    for (const root of [".claude", ".codex", ".grok", ".agents"]) {
      for (const name of ["CLAUDE.md", "AGENTS.md", "AGENTS.override.md", "GROK.md", "agents", "rules", "commands", "prompts", "skills"]) {
        const path = join(home, root, name);
        checkDirectory(home, dirname(path));
        const status = fs.lstatSync(path, { throwIfNoEntry: false });
        if (!status) continue;
        if (((root === ".codex" && name === "skills") || (root === ".grok" && name === "agents")) && status.isDirectory()) {
          for (const child of fs.readdirSync(path)) {
            const destination = join(path, child);
            if (!(root === ".codex" && child === ".system") && !artifacts.has(destination)) artifacts.set(destination, undefined);
          }
        } else artifacts.set(path, undefined);
      }
    }
    const codexSkills = join(home, ".codex-dev/skills");
    checkDirectory(home, codexSkills);
    if (fs.existsSync(codexSkills)) {
      for (const name of fs.readdirSync(codexSkills)) {
        const path = join(codexSkills, name);
        if (name !== ".system" && !artifacts.has(path)) artifacts.set(path, undefined);
      }
    }
    artifacts.set(join(home, ".codex-dev/AGENTS.override.md"), undefined);

    // Grok can discover user plugins directly, without installed_plugins.json.
    for (const root of [".claude", ".claude-dev", ".grok", ".grok-dev"]) {
      const directory = join(home, root, "plugins");
      checkDirectory(home, directory);
      if (!fs.existsSync(directory)) continue;
      for (const name of fs.readdirSync(directory)) {
        if (name === "cache" || name === "data") continue;
        const path = join(directory, name);
        const status = fs.lstatSync(path);
        const markers = [".claude-plugin/plugin.json", ".grok-plugin/plugin.json", "plugin.json", "skills", "commands", "agents", "hooks/hooks.json", ".mcp.json", ".lsp.json"];
        if (status.isSymbolicLink() || (status.isDirectory() && markers.some(marker => fs.existsSync(join(path, marker))))) {
          artifacts.set(path, undefined);
        }
      }
    }

    for (const relativePath of [".claude.json", ".claude/settings.json", ".claude/settings.local.json", ".claude-dev/.claude.json", ".claude-dev/settings.json"]) {
      const path = join(home, relativePath);
      checkDirectory(home, dirname(path));
      const previous = readConfiguration(path, "JSON");
      if (!previous) continue;
      const pending = artifacts.get(path);
      const value = pending ? JSON.parse((pending.data as Buffer).toString()) : { ...previous.value };
      const keys = basename(path) === ".claude.json" ? ["mcpServers"] : ["mcpServers", "hooks", "enabledPlugins", "skillOverrides"];
      if (!keys.some(key => key in value)) continue;
      if (!previous.status.isFile()) throw new Error(`refusing to replace non-regular ${path}`);
      for (const key of keys) delete value[key];
      artifacts.set(path, { mode: previous.status.mode & 0o7777, data: Buffer.from(`${JSON.stringify(value, null, 2)}\n`) });
    }

    for (const root of [".claude", ".claude-dev"]) {
      const path = join(home, root, "plugins/installed_plugins.json");
      checkDirectory(home, dirname(path));
      const previous = readConfiguration(path, "JSON");
      if (!previous || !("plugins" in previous.value)) continue;
      const plugins = previous.value.plugins;
      if (!plugins || typeof plugins !== "object" || Array.isArray(plugins)) throw new Error(`expected plugin registrations: ${path}`);
      const retained: Record<string, unknown> = {};
      let changed = false;
      for (const [name, entries] of Object.entries(plugins)) {
        if (!Array.isArray(entries) || entries.some(entry => !entry || typeof entry !== "object" || typeof entry.scope !== "string")) {
          throw new Error(`expected scoped plugin registrations: ${path}`);
        }
        const keep = entries.filter(entry => entry.scope !== "user");
        if (keep.length === entries.length) retained[name] = entries;
        else {
          changed = true;
          if (keep.length) retained[name] = keep;
        }
      }
      if (!changed) continue;
      if (!previous.status.isFile()) throw new Error(`refusing to replace non-regular ${path}`);
      artifacts.set(path, { mode: previous.status.mode & 0o7777, data: Buffer.from(`${JSON.stringify({ ...previous.value, plugins: retained }, null, 2)}\n`) });
    }

    for (const client of ["codex", "grok"]) {
      const path = join(home, `.${client}/config.toml`);
      checkDirectory(home, dirname(path));
      const previous = readConfiguration(path, "TOML");
      if (!previous || !("mcp_servers" in previous.value)) continue;
      const servers = previous.value.mcp_servers;
      if (!servers || typeof servers !== "object" || Array.isArray(servers)) throw new Error(`expected MCP registrations: ${path}`);
      const names = Object.keys(servers);
      if (!names.length) continue;
      if (!previous.status.isFile()) throw new Error(`refusing to replace non-regular ${path}`);
      const temporary = fs.mkdtempSync(join(tmpdir(), "dev-profile-mcp-"));
      try {
        const config = join(temporary, "config.toml");
        fs.writeFileSync(config, previous.data, { flag: "wx", mode: 0o600 });
        for (const name of names) {
          const args = client === "grok" ? ["mcp", "remove", "--scope", "user", name] : ["mcp", "remove", name];
          const result = await new Promise<{ code: number | null; signal: string | null; error?: Error }>(resolve => {
            const child = spawn(client, args, {
              cwd: temporary, env: { ...process.env, HOME: temporary, CODEX_HOME: temporary, GROK_HOME: temporary },
              stdio: "ignore", detached: true,
            });
            // CLI launchers may spawn a native binary; terminate the entire group on timeout.
            const timer = setTimeout(() => { if (child.pid) process.kill(-child.pid, "SIGKILL"); }, 15000);
            child.once("error", error => { clearTimeout(timer); resolve({ code: null, signal: null, error }); });
            child.once("exit", (code, signal) => { clearTimeout(timer); resolve({ code, signal }); });
          });
          if (result.error || result.code !== 0) {
            const cause = result.error ? ("code" in result.error ? result.error.code : result.error.name) : `exit ${result.code ?? result.signal}`;
            throw new Error(`cannot remove MCP registrations from ${path}: ${client} mcp remove failed (${cause}); native output withheld to protect configuration values`);
          }
        }
        const updated = readConfiguration(config, "TOML")!;
        const expected = { ...previous.value };
        delete expected.mcp_servers;
        const actual = { ...updated.value };
        if (actual.mcp_servers && typeof actual.mcp_servers === "object" && Object.keys(actual.mcp_servers).length === 0) delete actual.mcp_servers;
        if (!isDeepStrictEqual(actual, expected)) throw new Error(`MCP removal changed unrelated configuration or left registrations: ${path}`);
        artifacts.set(path, { mode: previous.status.mode & 0o7777, data: updated.data });
      } finally {
        fs.rmSync(temporary, { recursive: true, force: true });
      }
    }
  }

  // Validate every input and destination parent before creating or replacing anything.
  for (const path of artifacts.keys()) checkDirectory(home, dirname(path));
  const changed = [...artifacts].filter(([path, resource]) => resource ? !matches(path, resource) : fs.lstatSync(path, { throwIfNoEntry: false }));
  const previous = changed.filter(([path]) => fs.lstatSync(path, { throwIfNoEntry: false }));
  const directory = join(home, ".local/state/claude-dev/backups");
  if (previous.length) checkDirectory(home, directory);
  if (dryRun) {
    for (const [path, resource] of changed) {
      if (fs.lstatSync(path, { throwIfNoEntry: false })) console.log(`Would back up: ${path}`);
      if (resource) console.log(`Would write: ${path}`);
      else console.log(`Would remove: ${path}`);
    }
    if (!changed.length) console.log("No managed files changed.");
    console.log("Dry run: no installation paths changed.");
    return;
  }
  for (const [path] of changed) checkWritable(dirname(path));
  let backup: string | undefined;
  if (previous.length) {
    checkWritable(directory);
    fs.mkdirSync(directory, { recursive: true });
    backup = fs.mkdtempSync(join(directory, "install-"));
    console.log(`Backup: ${backup}`);
  }

  for (const [path, resource] of changed) {
    fs.mkdirSync(dirname(path), { recursive: true });
    const temporary = join(dirname(path), `.${basename(path)}.${randomUUID()}`);
    try {
      if (resource) writeResource(temporary, resource);
      if (fs.lstatSync(path, { throwIfNoEntry: false })) {
        const saved = join(backup!, relative(home, path));
        fs.mkdirSync(dirname(saved), { recursive: true });
        fs.renameSync(path, saved);
        console.log(`  backed up: ${path} -> ${saved}`);
      }
      if (resource) fs.renameSync(temporary, path);
    } finally {
      fs.rmSync(temporary, { recursive: true, force: true });
    }
    console.log(`  ${resource ? "wrote" : "removed"}: ${path}`);
  }
  console.log(`Installed ${targets.map(client => `${client}-dev`).join(", ")}. Ensure ${join(home, ".local/bin")} is on PATH.`);
  if (!changed.length) console.log("No managed files changed.");
}

const usage = "Usage: install.sh [--target claude|codex|grok|all] [--home DIR] [--clean-legacy] [--dry-run]\nInstall native development profiles.\n\n  --target NAME   profile to install (default: claude)\n  --home DIR      target runtime HOME (does not change process HOME)\n  --clean-legacy  back up and remove old user extensions; requires --target all\n  --dry-run       validate and show planned changes without publishing them\n  -h, --help      show this help";
let options;
try {
  options = parseArgs({ options: { home: { type: "string", default: homedir() }, target: { type: "string", default: "claude" },
    "clean-legacy": { type: "boolean" }, "dry-run": { type: "boolean" },
    help: { type: "boolean", short: "h" } } }).values;
  if (!["claude", "codex", "grok", "all"].includes(options.target!)) throw new Error("--target must be claude, codex, grok, or all");
  if (options["clean-legacy"] && options.target !== "all") throw new Error("--clean-legacy requires --target all");
} catch (error) {
  console.error(`${usage}\ninstall: ${(error as Error).message}`);
  process.exit(2);
}
if (options.help) {
  console.log(usage);
  process.exit(0);
}
let home = options.home!;
if (home === "~" || home.startsWith("~/")) home = homedir() + home.slice(1);
else if (home.startsWith("~")) throw new Error("--home: expand ~user in your shell or pass an absolute path");
await install(canonicalPath(isAbsolute(home) ? home : `${process.cwd()}/${home}`), options.target!,
  !!options["clean-legacy"], !!options["dry-run"]);
