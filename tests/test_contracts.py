"""Check published resources and Claude tool boundaries, not model behavior."""

from pathlib import Path
import re
import unittest


TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
ROLE_TOOLS = {
    "research": {"Read", "Grep", "Glob", "WebSearch", "WebFetch"},
    "arch": {"Read", "Grep", "Glob", "WebSearch", "WebFetch"},
    "dev": {"Read", "Grep", "Glob", "Edit", "Write", "Bash"},
    "simplify": {"Read", "Grep", "Glob", "Edit", "Write", "Bash"},
    "review": {"Read", "Grep", "Glob"},
}


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
            metadata[key] = value
        self.assertEqual(set(metadata), fields, str(path))
        self.assertTrue("\n".join(lines[end + 1:]).strip(), str(path))
        return metadata

    def test_profile_contains_only_current_components(self):
        self.assertEqual({path.name for path in TEMPLATES.iterdir()},
                         {"CLAUDE.md", "agents", "skills", "codex", "grok"})
        self.assertTrue((TEMPLATES / "CLAUDE.md").read_text().strip())
        self.assertEqual({path.name for path in (TEMPLATES / "agents").iterdir()},
                         {f"{role}.md" for role in ROLE_TOOLS})
        self.assertEqual({path.name for path in (TEMPLATES / "skills").iterdir()}, {"develop"})

    def test_roles_inherit_model_and_have_only_assigned_tools(self):
        for role, expected in ROLE_TOOLS.items():
            with self.subTest(role=role):
                metadata = self.frontmatter(TEMPLATES / "agents" / f"{role}.md",
                                            {"name", "description", "tools", "model"})
                self.assertEqual(metadata["name"], role)
                self.assertEqual(metadata["model"], "inherit")
                tools = [name.strip() for name in metadata["tools"].split(",")]
                self.assertEqual(len(tools), len(set(tools)))
                self.assertEqual(set(tools), expected)

    def test_develop_has_discovery_metadata(self):
        metadata = self.frontmatter(TEMPLATES / "skills/develop/SKILL.md", {"name", "description"})
        self.assertEqual(metadata["name"], "develop")

    def test_relative_markdown_links_resolve_inside_templates(self):
        for path in TEMPLATES.rglob("*.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(source=path, target=target):
                    resolved = (path.parent / target.split("#", 1)[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(TEMPLATES.resolve()))
                    self.assertTrue(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
