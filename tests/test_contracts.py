"""Static template format and reference checks, not agent behavior evaluation."""

import graphlib
from pathlib import Path
import re
import unittest


TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
ROLES = {"arch", "dev", "review", "research", "refine", "plan"}
SKILLS = {"orchestrate", "author-skills"}


class TemplateContractTests(unittest.TestCase):
    def frontmatter(self, path, fields):
        lines = path.read_text().splitlines()
        self.assertEqual(lines[0], "---", str(path))
        end = lines.index("---", 1)
        metadata = {}
        for line in lines[1:end]:
            key, separator, value = line.partition(": ")
            self.assertEqual(separator, ": ", str(path))
            self.assertNotIn(key, metadata, str(path))
            self.assertTrue(value.strip(), str(path))
            self.assertEqual(value, value.strip(), str(path))
            self.assertNotIn(value[0], "\"'[{>|&*!#", str(path))
            self.assertNotIn(": ", value, str(path))
            self.assertNotIn(" #", value, str(path))
            metadata[key] = value
        self.assertEqual(set(metadata), fields, str(path))
        self.assertTrue("\n".join(lines[end + 1:]).strip(), str(path))
        return metadata

    def test_roles_have_one_source_and_inherit_model(self):
        paths = sorted((TEMPLATES / "agents").glob("*.md"))
        self.assertEqual({path.stem for path in paths}, ROLES)
        self.assertFalse((TEMPLATES / "codex-agents").exists())
        for path in paths:
            with self.subTest(role=path.stem):
                metadata = self.frontmatter(path, {"name", "description", "model"})
                self.assertEqual(metadata["name"], path.stem)
                self.assertEqual(metadata["model"], "inherit")

    def test_skills_have_portable_metadata(self):
        paths = sorted((TEMPLATES / "skills").glob("*/SKILL.md"))
        self.assertEqual({path.parent.name for path in paths}, SKILLS)
        for path in paths:
            with self.subTest(skill=path.parent.name):
                metadata = self.frontmatter(path, {"name", "description"})
                self.assertEqual(metadata["name"], path.parent.name)
                self.assertRegex(metadata["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertLessEqual(len(metadata["name"]), 64)

    def test_relative_markdown_links_resolve_inside_templates(self):
        for path in TEMPLATES.rglob("*.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(source=path, target=target):
                    resolved = (path.parent / target.split("#", 1)[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(TEMPLATES.resolve()))
                    self.assertTrue(resolved.is_file())

    def test_plan_role_and_skill_share_the_same_format_reference(self):
        reference = TEMPLATES / "skills/orchestrate/references/plan-format.md"
        self.assertTrue(reference.is_file())
        for path in (TEMPLATES / "agents/plan.md", TEMPLATES / "skills/orchestrate/SKILL.md"):
            links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text())
            self.assertIn(reference.resolve(), [(path.parent / link).resolve() for link in links])

    def test_plan_example_is_a_consistent_task_graph(self):
        reference = TEMPLATES / "skills/orchestrate/references/plan-format.md"
        example = reference.read_text().split("```markdown\n", 1)[1].split("```", 1)[0]
        tasks = {}
        for line in example.splitlines():
            if not line.startswith("- [") or "`id:" not in line:
                continue
            match = re.fullmatch(
                r"- \[([ x])\] \(([a-z]+)\) `id: ([a-z0-9-]+)`; "
                r"`deps: \[([^]]*)\]`; `owns: \[([^]]*)\]`; `state: ([a-z]+)`", line,
            )
            self.assertIsNotNone(match, line)
            checked, role, task_id, deps, owns, state = match.groups()
            self.assertNotIn(task_id, tasks)
            self.assertIn(role, ROLES)
            self.assertIn(state, {"pending", "running", "blocked", "done"})
            self.assertEqual(checked == "x", state == "done")
            if role == "review":
                self.assertEqual(owns, "")
            tasks[task_id] = deps.split(", ") if deps else []
        self.assertTrue(tasks)
        for deps in tasks.values():
            self.assertTrue(set(deps) <= tasks.keys())
        self.assertEqual(set(graphlib.TopologicalSorter(tasks).static_order()), tasks.keys())
        self.assertEqual(len(re.findall(r"^  Acceptance: .+", example, re.MULTILINE)), len(tasks))


if __name__ == "__main__":
    unittest.main()
