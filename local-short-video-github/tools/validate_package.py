#!/usr/bin/env python3
"""Offline validation for the GitHub distribution package."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


REQUIRED_SCRIPTS = {
    "audition_voices.py",
    "create_contact_sheet.py",
    "create_pop_ass.py",
    "create_project.py",
    "normalize_subtitles.py",
    "preflight_local_video.py",
    "preflight_local_video.ps1",
    "render_local_video.py",
    "select_assets.py",
    "synthesize_voice.py",
    "update_asset_usage.py",
    "validate_final.py",
    "video_common.py",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    skill = root / "skills" / "local-short-video"
    skill_md = skill / "SKILL.md"
    agent_yaml = skill / "agents" / "openai.yaml"
    scripts = skill / "scripts"

    for path in [skill_md, agent_yaml, scripts]:
        if not path.exists():
            fail(f"required path is missing: {path.relative_to(root)}")

    text = skill_md.read_text(encoding="utf-8-sig")
    match = re.match(r"^---\n(?P<frontmatter>.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md frontmatter is missing or malformed")
    keys = []
    values = {}
    for line in match.group("frontmatter").splitlines():
        if ":" not in line:
            fail(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        keys.append(key.strip())
        values[key.strip()] = value.strip()
    if keys != ["name", "description"]:
        fail("SKILL.md frontmatter must contain only name and description")
    if values["name"] != skill.name:
        fail("skill folder and frontmatter name do not match")
    if len(values["description"]) < 40:
        fail("skill description is too short")

    agent_text = agent_yaml.read_text(encoding="utf-8-sig")
    if "$local-short-video" not in agent_text:
        fail("agents/openai.yaml default prompt must mention $local-short-video")

    present_scripts = {path.name for path in scripts.iterdir() if path.is_file()}
    missing = sorted(REQUIRED_SCRIPTS - present_scripts)
    if missing:
        fail("missing scripts: " + ", ".join(missing))

    forbidden = [path for path in skill.rglob("*") if path.name == "__pycache__" or path.suffix == ".pyc"]
    if forbidden:
        fail("generated Python cache files are present")

    for path in skill.rglob("*.py"):
        source = path.read_text(encoding="utf-8-sig")
        try:
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            fail(f"Python syntax error in {path.relative_to(root)}: {exc}")

    searchable = "\n".join(
        path.read_text(encoding="utf-8-sig", errors="replace")
        for path in skill.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".py", ".ps1", ".yaml", ".json"}
    )
    if "TODO" in searchable:
        fail("unresolved TODO marker found in skill")
    if re.search(r"Primer\s*Mall", searchable, re.IGNORECASE):
        fail("brand-specific Primer Mall text found in generic skill")

    print("Package validation passed")
    print(f"Skill: {values['name']}")
    print(f"Python scripts: {len(list(skill.rglob('*.py')))}")


if __name__ == "__main__":
    main()
