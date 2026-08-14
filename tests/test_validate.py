from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate as validator


SOURCE_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAMES = [f"sample-skill-{index:02d}" for index in range(1, 16)]


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.build_valid_repository()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: object) -> None:
        self.write(relative, json.dumps(value, indent=2) + "\n")

    def build_valid_repository(self) -> None:
        catalog_skills = {}
        route_skills = {}
        positive = {}
        for index, name in enumerate(SKILL_NAMES, start=1):
            description = f"Reusable sample skill number {index}."
            self.write(
                f"skills/{name}/SKILL.md",
                "\n".join(
                    [
                        "---",
                        f"name: {name}",
                        f'description: "{description}"',
                        "license: MIT",
                        "---",
                        "",
                        f"# Sample skill {index}",
                        "",
                    ]
                ),
            )
            catalog_skills[name] = {"path": f"skills/{name}"}
            keyword = f"route-token-{index:02d}-done"
            route_skills[name] = {
                "priority": "medium",
                "promptTriggers": {"keywords": [keyword], "intentPatterns": []},
                "fileTriggers": {"pathPatterns": [], "pathExclusions": []},
            }
            positive[f"please use {keyword}"] = [name]

        self.write("agents/helper.md", "# Helper\n")
        self.write("templates/CLAUDE.md", "# Claude rules\n")
        self.write("templates/AGENTS.md", "# Agent rules\n")
        self.write("hooks/merge-guard.py", "VALUE = 1\n")
        self.write("hooks/skill-usage-log.py", "VALUE = 1\n")
        source_hook = SOURCE_ROOT / "hooks" / "skill-activation.py"
        target_hook = self.root / "hooks" / "skill-activation.py"
        target_hook.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_hook, target_hook)

        self.write_json(
            "catalog.json",
            {
                "schemaVersion": 1,
                "name": "ai-skills-assembly",
                "displayName": "AI Skills Assembly",
                "surfaces": {"skills": ["agents", "claude", "codex"], "agents": ["claude", "codex"]},
                "skills": catalog_skills,
                "agents": {"helper": {"path": "agents/helper.md"}},
                "profiles": {"default": {"skills": SKILL_NAMES, "agents": ["helper"]}},
                "routing": {
                    "registry": "routing/skill-rules.json",
                    "fixtures": "routing/routing-expectations.json",
                },
                "globalRules": {
                    "claude": "templates/CLAUDE.md",
                    "codex": "templates/AGENTS.md",
                },
                "hooks": {
                    "activation": "hooks/skill-activation.py",
                    "mergeGuard": "hooks/merge-guard.py",
                    "usage": "hooks/skill-usage-log.py",
                },
            },
        )
        self.write_json("routing/skill-rules.json", {"version": "1.0", "skills": route_skills})
        self.write_json(
            "routing/routing-expectations.json",
            {"version": "1.0", "positive": positive, "negative": ["an unrelated prompt"]},
        )

    def add_catalog_skill(self, name: str, include_in_default: bool = True) -> None:
        self.write(
            f"skills/{name}/SKILL.md",
            f'---\nname: {name}\ndescription: "Reusable extra skill."\nlicense: MIT\n---\n',
        )
        catalog = self.read_json("catalog.json")
        catalog["skills"][name] = {"path": f"skills/{name}"}
        if include_in_default:
            catalog["profiles"]["default"]["skills"].append(name)
        self.write_json("catalog.json", catalog)

        registry = self.read_json("routing/skill-rules.json")
        registry["skills"][name] = {
            "priority": "medium",
            "promptTriggers": {"keywords": ["extra-route-token"], "intentPatterns": []},
            "fileTriggers": {"pathPatterns": [], "pathExclusions": []},
        }
        self.write_json("routing/skill-rules.json", registry)
        fixtures = self.read_json("routing/routing-expectations.json")
        fixtures["positive"]["please use extra-route-token"] = [name]
        self.write_json("routing/routing-expectations.json", fixtures)

    def errors_for(self, check: str) -> list[validator.Finding]:
        return [item for item in validator.validate(self.root) if item.check == check and item.severity == "error"]

    def test_valid_repository_passes(self) -> None:
        self.assertEqual([], validator.validate(self.root))

    def test_python_compile_failure_is_reported(self) -> None:
        self.write("scripts/broken.py", "if True print('broken')\n")

        self.assertTrue(self.errors_for("python"))

    def test_catalog_rejects_path_escape(self) -> None:
        catalog = self.read_json("catalog.json")
        catalog["skills"][SKILL_NAMES[0]]["path"] = "../outside"
        self.write_json("catalog.json", catalog)

        self.assertTrue(self.errors_for("catalog"))

    def test_catalog_requires_canonical_repository_slug(self) -> None:
        cases = (
            (42, "name must be a string"),
            ("ai-skills", "name must be 'ai-skills-assembly'"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                catalog = self.read_json("catalog.json")
                catalog["name"] = value
                self.write_json("catalog.json", catalog)

                findings = self.errors_for("catalog")

                self.assertTrue(any(expected in item.message for item in findings))
                catalog["name"] = "ai-skills-assembly"
                self.write_json("catalog.json", catalog)

    def test_catalog_requires_canonical_display_name(self) -> None:
        cases = (
            ([], "displayName must be a string"),
            ("AI Skills", "displayName must be 'AI Skills Assembly'"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                catalog = self.read_json("catalog.json")
                catalog["displayName"] = value
                self.write_json("catalog.json", catalog)

                findings = self.errors_for("catalog")

                self.assertTrue(any(expected in item.message for item in findings))
                catalog["displayName"] = "AI Skills Assembly"
                self.write_json("catalog.json", catalog)

    def test_catalog_requires_skill_license(self) -> None:
        path = self.root / "skills" / SKILL_NAMES[0] / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8").replace("license: MIT\n", ""), encoding="utf-8")

        self.assertTrue(self.errors_for("catalog"))

    def test_catalog_validates_hook_paths(self) -> None:
        catalog = self.read_json("catalog.json")
        catalog["hooks"]["activation"] = "../outside.py"
        self.write_json("catalog.json", catalog)

        self.assertTrue(self.errors_for("catalog"))

    def test_catalog_path_maps_require_string_values(self) -> None:
        catalog = self.read_json("catalog.json")
        catalog["hooks"]["activation"] = {"path": "hooks/skill-activation.py"}
        self.write_json("catalog.json", catalog)

        findings = self.errors_for("catalog")
        self.assertTrue(any("must be a string path" in item.message for item in findings))

    def test_catalog_requires_global_rule_keys(self) -> None:
        catalog = self.read_json("catalog.json")
        del catalog["globalRules"]["codex"]
        self.write_json("catalog.json", catalog)

        findings = self.errors_for("catalog")
        self.assertTrue(any("globalRules is missing required keys" in item.message for item in findings))

    def test_catalog_requires_hook_keys(self) -> None:
        catalog = self.read_json("catalog.json")
        del catalog["hooks"]["usage"]
        self.write_json("catalog.json", catalog)

        findings = self.errors_for("catalog")
        self.assertTrue(any("hooks is missing required keys" in item.message for item in findings))

    def test_catalog_validates_every_profile(self) -> None:
        catalog = self.read_json("catalog.json")
        catalog["profiles"]["broken-profile"] = {"skills": ["missing-skill"], "agents": []}
        self.write_json("catalog.json", catalog)

        findings = self.errors_for("catalog")
        self.assertTrue(any("profiles.broken-profile.skills" in item.message for item in findings))

    def test_catalog_allows_default_profile_to_grow(self) -> None:
        self.add_catalog_skill("sample-skill-extra")

        self.assertEqual([], validator.validate(self.root))

    def test_default_profile_must_include_every_skill(self) -> None:
        self.add_catalog_skill("sample-skill-extra", include_in_default=False)

        findings = self.errors_for("catalog")
        self.assertTrue(any("default profile omits public skills" in item.message for item in findings))

    def test_stray_skill_directory_is_reported(self) -> None:
        self.write("skills/stray-skill/notes.txt", "not a skill\n")

        findings = self.errors_for("catalog")
        self.assertTrue(any("uncataloged skill directories" in item.message for item in findings))

    def test_routing_fixture_mismatch_is_reported(self) -> None:
        fixtures = self.read_json("routing/routing-expectations.json")
        first_prompt = next(iter(fixtures["positive"]))
        fixtures["positive"][first_prompt] = [SKILL_NAMES[1]]
        self.write_json("routing/routing-expectations.json", fixtures)

        self.assertTrue(self.errors_for("routing"))

    def test_missing_routing_rule_is_reported(self) -> None:
        registry = self.read_json("routing/skill-rules.json")
        missing = SKILL_NAMES[0]
        del registry["skills"][missing]
        self.write_json("routing/skill-rules.json", registry)
        fixtures = self.read_json("routing/routing-expectations.json")
        fixtures["positive"] = {
            prompt: expected
            for prompt, expected in fixtures["positive"].items()
            if missing not in expected
        }
        self.write_json("routing/routing-expectations.json", fixtures)

        findings = self.errors_for("routing")
        self.assertTrue(any("catalog skills lack routing rules" in item.message for item in findings))

    def test_listing_budget_overflow_is_reported(self) -> None:
        description = "x" * 600
        for name in SKILL_NAMES:
            path = self.root / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                next(line for line in text.splitlines() if line.startswith("description:")),
                f'description: "{description}"',
            )
            path.write_text(text, encoding="utf-8")

        self.assertTrue(self.errors_for("listing"))

    def test_external_symlink_is_reported(self) -> None:
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "target.txt"
        target.write_text("outside\n", encoding="utf-8")
        (self.root / "escape").symlink_to(target)

        self.assertTrue(self.errors_for("symlink"))

    def test_non_ascii_dash_is_reported(self) -> None:
        self.write("bad-copy.md", "left" + chr(0x2014) + "right\n")

        self.assertTrue(self.errors_for("hyphens"))

    def test_absolute_home_paths_are_reported(self) -> None:
        posix_path = "/" + "home" + "/sample-user/private.txt"
        root_path = "/" + "root" + "/private.txt"
        windows_path = "C:" + "\\" + "Users" + "\\sample-user\\private.txt"
        self.write("privacy.txt", f"{posix_path}\n{root_path}\n{windows_path}\n")

        self.assertGreaterEqual(len(self.errors_for("privacy")), 3)

    def test_non_utf8_artifact_is_reported(self) -> None:
        path = self.root / "artifact.bin"
        path.write_bytes(bytes((0xFF, 0xFE, 0xFD)))

        findings = self.errors_for("privacy")
        self.assertTrue(any("non-UTF-8" in item.message for item in findings))

    def test_binary_control_character_is_reported(self) -> None:
        path = self.root / "artifact.dat"
        path.write_bytes(b"text\x00payload")

        findings = self.errors_for("privacy")
        self.assertTrue(any("binary control character" in item.message for item in findings))

    def test_secret_signature_is_reported_without_value(self) -> None:
        candidate = "ghp_" + ("A" * 36)
        self.write("secret.txt", candidate + "\n")

        findings = self.errors_for("secrets")
        self.assertTrue(findings)
        self.assertNotIn(candidate, "\n".join(item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
