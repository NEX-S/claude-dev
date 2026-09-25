#!/usr/bin/env bun
import * as fs from "node:fs";
import { createHash, randomUUID } from "node:crypto";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, join, relative } from "node:path";
import { parseArgs } from "node:util";

const ROOT = dirname(import.meta.dir);
const ROLES = ["arch", "dev", "plan", "refine", "research", "review"];
const utf8 = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
type Artifact = { path: string; content: Buffer; mode: number };

function frontmatter(path: string, fields: string[]) {
  const text = utf8.decode(fs.readFileSync(path));
  const end = text.indexOf("\n---\n", 3);
  if (!text.startsWith("---\n") || end < 0) {
    throw new Error(`${path}: expected a closed frontmatter block`);
  }
  const metadata: Record<string, string> = {};
  for (const line of text.slice(4, end).split("\n")) {
    const match = /^([a-z][a-z-]*): (\S(?:.*\S)?)$/.exec(line);
    if (!match) throw new Error(`${path}: expected a single-line plain field: ${JSON.stringify(line)}`);
    const [, key, value] = match;
    if (Object.hasOwn(metadata, key) || !fields.includes(key)) {
      throw new Error(`${path}: duplicate or unsupported field: ${key}`);
    }
    if ("!&*[{>|\"'%@`#".includes(value[0]) || value.includes(": ") || value.includes(" #")) {
      throw new Error(`${path}: unsupported YAML syntax in ${key}`);
    }
    metadata[key] = value;
  }
  const body = text.slice(end + 5);
  if (fields.some(field => !Object.hasOwn(metadata, field)) || !body.trim()) {
    throw new Error(`${path}: expected fields ${fields.join(", ")} and a nonempty body`);
  }
  return { metadata, body };
}

const ALIAS_VARIABLES = ["ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
  "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"];

// A session that names one model still resolves the native opus/sonnet/haiku aliases for
// built-in subagents and the auto-mode classifier. Those become Anthropic model ids, which an
// endpoint that only serves its own model names rejects. Pin every alias to the requested model.
function claudeWrapper(destination: string) {
  return [
    "#!/bin/sh",
    `export CLAUDE_CONFIG_DIR='${destination}'`,
    "model=",
    "previous=",
    'for argument in "$@"; do',
    '    case $argument in --) break ;; esac',
    '    case $previous in --model) model=$argument ;; esac',
    '    case $argument in --model=*) model=${argument#--model=} ;; esac',
    "    previous=$argument",
    "done",
    'if [ -n "$model" ]; then',
    ...ALIAS_VARIABLES.map(name => `    export ${name}="$model"`),
    "fi",
    "exec claude --permission-mode bypassPermissions --effort max --autocompact 900k \"$@\"",
  ].join("\n") + "\n";
}

function artifacts(home: string): Artifact[] {
  const template = join(ROOT, "templates");
  const root = fs.readFileSync(join(template, "AGENTS.md"));
  if (!root.some(byte => ![9, 10, 11, 12, 13, 32].includes(byte))) {
    throw new Error("templates/AGENTS.md must not be empty");
  }
  const files: Artifact[] = [];
  const add = (path: string, content: Buffer, mode = 0o644) => files.push({ path: join(home, path), content, mode });
  add(".claude-dev/CLAUDE.md", root);
  add(".codex-dev/AGENTS.md", root);
  for (const role of ROLES) {
    const source = join(template, "agents", `${role}.md`);
    const { metadata, body } = frontmatter(source, ["name", "description", "model"]);
    if (metadata.name !== role || metadata.model !== "inherit") {
      throw new Error(`${source}: name must match its filename and model must be inherit`);
    }
    add(`.claude-dev/agents/${role}.md`, fs.readFileSync(source));
    const codex = { name: role, description: metadata.description, developer_instructions: body };
    const toml = Object.entries(codex).map(([key, value]) => `${key} = ${JSON.stringify(value)}\n`).join("");
    add(`.codex-dev/agents/${role}.toml`, Buffer.from(toml.replaceAll("\x7f", "\\u007f")));
  }
  for (const skill of fs.readdirSync(join(template, "skills"), { withFileTypes: true })
    .filter(entry => entry.isDirectory() && !entry.name.startsWith("."))
    .map(entry => entry.name)
    .sort()) {
    const directory = join(template, "skills", skill);
    const { metadata } = frontmatter(join(directory, "SKILL.md"), ["name", "description"]);
    if (metadata.name !== skill) throw new Error(`${directory}: skill name must match its directory`);
    function copyResources(current: string) {
      for (const name of fs.readdirSync(current).sort()) {
        const source = join(current, name);
        const status = fs.lstatSync(source);
        if (status.isDirectory()) copyResources(source);
        else if (status.isFile()) {
          for (const client of ["claude", "codex"]) {
            add(`.${client}-dev/skills/${skill}/${relative(directory, source)}`, fs.readFileSync(source), status.mode & 0o7777);
          }
        } else throw new Error(`${source}: skill resources must be regular files or directories`);
      }
    }
    copyResources(directory);
  }
  for (const [client, variable] of [["claude", "CLAUDE_CONFIG_DIR"], ["codex", "CODEX_HOME"]]) {
    const destination = join(home, `.${client}-dev`).replaceAll("'", "'\"'\"'");
    const wrapper = client === "claude" ? claudeWrapper(destination)
      : `#!/bin/sh\nexport ${variable}='${destination}'\nexec ${client} "$@"\n`;
    add(`.local/bin/${client}-dev`, Buffer.from(wrapper), 0o755);
  }
  return files;
}

function directoryProblem(home: string, directory: string): string | undefined {
  if (directory !== home) {
    const parentProblem = directoryProblem(home, dirname(directory));
    if (parentProblem) return parentProblem;
  }
  const status = fs.lstatSync(directory, { throwIfNoEntry: false });
  if (status && !status.isDirectory()) return directory;
}

// Follow each link before applying ..; Bun realpath normalizes .. too early.
// Missing suffixes are allowed because the installation root may not exist yet.
function canonicalPath(path: string, activeLinks = new Set<string>()): string {
  let resolved = "/";
  for (const part of path.split("/")) {
    if (!part || part === ".") continue;
    if (part === "..") {
      resolved = dirname(resolved);
      continue;
    }
    const next = join(resolved, part);
    if (fs.lstatSync(next, { throwIfNoEntry: false })?.isSymbolicLink()) {
      if (activeLinks.has(next)) throw Object.assign(new Error(`symbolic link loop: ${next}`), { code: "ELOOP" });
      activeLinks.add(next);
      const target = fs.readlinkSync(next);
      resolved = canonicalPath(isAbsolute(target) ? target : `${resolved}/${target}`, activeLinks);
      activeLinks.delete(next);
    } else resolved = next;
  }
  return resolved;
}

function legacyCandidates(home: string) {
  const manifest = JSON.parse(utf8.decode(fs.readFileSync(join(ROOT, "scripts/legacy-files.json")))) as {
    files: Record<string, { sha256: string }[]>;
    forwarder: { sha256: string };
  };
  const hashes = new Map(Object.entries(manifest.files).map(([path, versions]) => [path, new Set(versions.map(v => v.sha256))]));
  const digest = (path: string) => createHash("sha256").update(fs.readFileSync(path)).digest("hex");
  const known: string[] = [], retained: string[] = [];
  // Prove the association before any move makes the old target disappear.
  const target = join(home, ".claude/AGENTS.md");
  const targetKnown = !directoryProblem(home, dirname(target))
    && fs.lstatSync(target, { throwIfNoEntry: false })?.isFile()
    && hashes.get(".claude/AGENTS.md")!.has(digest(target));
  for (const path of [...hashes.keys(), ".codex/AGENTS.md"]) {
    const absolute = join(home, path);
    if (directoryProblem(home, dirname(absolute))) {
      retained.push(absolute);
      continue;
    }
    const status = fs.lstatSync(absolute, { throwIfNoEntry: false });
    if (!status) continue;
    let matched = false;
    if (status.isSymbolicLink()) {
      const link = fs.readlinkSync(absolute);
      if (path === ".codex/AGENTS.md" && isAbsolute(link) && targetKnown) {
        try {
          matched = fs.statSync(absolute).isFile() && canonicalPath(link) === target;
        } catch (error) {
          // Broken or cyclic user links cannot prove ownership and must be retained.
          if (!["ENOENT", "ENOTDIR", "ELOOP"].includes((error as NodeJS.ErrnoException).code!)) throw error;
        }
      }
    } else if (status.isFile()) {
      const hash = digest(absolute);
      matched = hashes.get(path)?.has(hash) ?? false;
      if (path === ".claude/CLAUDE.md" && hash === manifest.forwarder.sha256) matched = !!targetKnown;
    }
    (matched ? known : retained).push(absolute);
  }
  return { known, retained };
}

function install(home: string) {
  const changed: Artifact[] = [];
  for (const file of artifacts(home)) {
    const problem = directoryProblem(home, dirname(file.path));
    if (problem) throw new Error(`refusing managed directory that is a symlink or non-directory: ${problem}`);
    const status = fs.lstatSync(file.path, { throwIfNoEntry: false });
    if (status && !status.isSymbolicLink() && !status.isFile()) throw new Error(`refusing non-file destination: ${file.path}`);
    if (status?.isFile() && fs.readFileSync(file.path).equals(file.content) && (status.mode & 0o7777) === file.mode) continue;
    changed.push(file);
  }
  const { known, retained } = legacyCandidates(home);
  const toBackup = [...changed.filter(file => fs.lstatSync(file.path, { throwIfNoEntry: false })).map(file => file.path), ...known];
  if (toBackup.length) {
    const directory = join(home, ".local/state/claudex/backups");
    const problem = directoryProblem(home, directory);
    if (problem) throw new Error(`refusing backup directory that is a symlink or non-directory: ${problem}`);
    fs.mkdirSync(directory, { recursive: true });
    const prefix = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z-");
    const backup = fs.mkdtempSync(join(directory, prefix));
    console.log(`Backup: ${backup}`);
    for (const path of toBackup) {
      const saved = join(backup, relative(home, path));
      fs.mkdirSync(dirname(saved), { recursive: true });
      fs.renameSync(path, saved);
      console.log(`  backed up: ${path} -> ${saved}`);
    }
  }
  for (const { path, content, mode } of changed) {
    fs.mkdirSync(dirname(path), { recursive: true });
    const temporary = join(dirname(path), `.${basename(path)}.${randomUUID()}`);
    const fd = fs.openSync(temporary, "wx", mode);
    try {
      try {
        fs.writeFileSync(fd, content);
        fs.fchmodSync(fd, mode);
      } finally {
        fs.closeSync(fd);
      }
      fs.renameSync(temporary, path);
    } finally {
      fs.rmSync(temporary, { force: true });
    }
    console.log(`  wrote: ${path}`);
  }
  if (retained.length) {
    console.log("Migration incomplete; retained unrecognized or user-owned paths:");
    for (const path of retained) console.log(`  ${path}`);
  }
  console.log(`Installed development commands. Ensure ${join(home, ".local/bin")} is on PATH.`);
  console.log("Use claude-dev / codex-dev; development profiles have separate login and service configuration.");
  if (!changed.length && !known.length) console.log("No managed files changed.");
}

const usage = "Usage: install.sh [--home DIR]\nInstall isolated Claude/Codex development instructions.\n\n  --home DIR  installation root (does not change process HOME)\n  -h, --help  show this help";
let options;
try {
  options = parseArgs({ options: { home: { type: "string", default: homedir() }, help: { type: "boolean", short: "h" } } }).values;
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
install(canonicalPath(isAbsolute(home) ? home : `${process.cwd()}/${home}`));
