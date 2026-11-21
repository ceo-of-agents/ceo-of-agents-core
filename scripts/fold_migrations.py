#!/usr/bin/env python3
"""Fold the notes in migrations/unreleased/ into the migration of the next version.

Run by the release workflow after release-please has bumped the version, and
usable by hand to preview (`python3 scripts/fold_migrations.py --dry-run`).
See CONTRIBUTING.md, "Every version ships a migration", and
migrations/README.md, "Unreleased changes".

Rules:
- version is the "version" in .claude-plugin/plugin.json. previous is the last
  version listed in migrations/README.md, "Current status" (paragraphs that
  start with "Version `X.Y.Z`").
- If version is already listed, nothing changes and the exit code is 0, so a
  second run is a no-op. If migrations/<previous>-to-<version>.md exists but the
  README has no entry for it, the script stops with an error: a person must
  finish that work.
- Notes are read from migrations/unreleased/*.md, ordered by the leading issue
  number, then by name. A note has a title line "# Unreleased: <what>", intro
  paragraphs before its first "## " heading (one of them is the schema line),
  a "Plain summary for the CEO:" line, any "## " sections, and a
  "## Check after applying" section with bullets. A note that lacks the title,
  the plain summary or the check section is an error.
- The script writes migrations/<previous>-to-<version>.md, appends one
  paragraph to "Current status" in migrations/README.md, and deletes the
  folded notes. With zero notes it writes a version-bump-only migration.
- The first intro paragraph of a note becomes its status text in the README, so
  write it as a summary.
- --dry-run prints the file and the paragraph and writes nothing.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"
UNRELEASED = MIGRATIONS / "unreleased"
SEMVER = r"\d+\.\d+\.\d+"
ENTRY = re.compile(rf"^Version `({SEMVER})`", re.MULTILINE)
TITLE = "# Unreleased:"
SUMMARY = "Plain summary for the CEO:"
CHECK = "## Check after applying"

APPLY_PARAGRAPH = (
    "Apply the sections below in order, all in one commit. In the hq the template placeholders are already "
    "rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly "
    "(the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask. "
    "If an edit's new text is already present (the hq was partly migrated before, or this is a second run), "
    "skip that edit silently, without asking: ask only when neither the old nor the new text is found."
)


class NoteError(Exception):
    pass


def key(version):
    return tuple(int(part) for part in version.split("."))


def lower_first(text):
    return text[:1].lower() + text[1:]


def upper_first(text):
    return text[:1].upper() + text[1:]


def split_sections(lines):
    """Split lines into (heading or None, body lines); a '## ' inside a code fence is not a heading."""
    sections = [[None, []]]
    fenced = False
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            sections.append([line.strip(), []])
        else:
            sections[-1][1].append(line)
    return sections


def demote(lines):
    out, fenced = [], False
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
        out.append("#" + line if not fenced and line.startswith("#") else line)
    return out


def paragraphs(lines):
    result, current = [], []
    for line in lines:
        if line.strip():
            current.append(line.rstrip())
        elif current:
            result.append("\n".join(current))
            current = []
    if current:
        result.append("\n".join(current))
    return result


def parse_note(path):
    """Parse one note; raise NoteError naming the note when its shape is wrong."""
    name = f"migrations/unreleased/{path.name}"
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((line for line in lines if line.strip()), "")
    if not title.startswith(TITLE) or not title[len(TITLE):].strip():
        raise NoteError(f"{name}: the first line must be '{TITLE} <what>'")
    what = title[len(TITLE):].strip().rstrip(".")

    summary = None
    kept = []
    for line in lines[lines.index(title) + 1:]:
        if line.startswith(SUMMARY):
            summary = line[len(SUMMARY):].strip()
        else:
            kept.append(line)
    if not summary:
        raise NoteError(f"{name}: no '{SUMMARY} ...' line")

    sections = split_sections(kept)
    intro = paragraphs(sections[0][1])
    checks = None
    body = []
    for heading, content in sections[1:]:
        if heading == CHECK:
            checks = [line.rstrip() for line in content if line.lstrip().startswith("- ")]
        else:
            body.append((heading, content))
    if checks is None:
        raise NoteError(f"{name}: no '{CHECK}' section")
    if not checks:
        raise NoteError(f"{name}: '{CHECK}' has no bullet")
    if not intro:
        raise NoteError(f"{name}: no intro paragraph between the title and the first '## ' heading")

    schema = next((p for p in intro if p.startswith(("No schema", "Schema"))), None)
    if schema is None:
        schema = next((p for p in intro if "schema version" in p.lower()), None)
    if schema is None:
        raise NoteError(f"{name}: no schema line (an intro paragraph such as 'No schema version changes: ...')")
    others = [p for p in intro if p != schema]
    if not others:
        raise NoteError(f"{name}: no intro paragraph besides the schema line")

    return {"name": path.name, "what": what, "intro": others, "schema": schema,
            "summary": summary, "body": body, "checks": checks}


def note_order(path):
    match = re.match(r"(\d+)", path.name)
    return (int(match.group(1)) if match else 10**9, path.name)


def read_notes():
    if not UNRELEASED.is_dir():
        return [], []
    paths = sorted(UNRELEASED.glob("*.md"), key=note_order)
    return paths, [parse_note(path) for path in paths]


def schema_lines(notes):
    found = []
    for note in notes:
        if note["schema"] not in found:
            found.append(note["schema"])
    return found or ["No schema version changes."]


def build_file(previous, version, notes):
    out = [f"# Migration {previous} to {version}", ""]
    if not notes:
        out += [f"Version {version} has no changes in the hq: this migration only bumps the version.", "",
                "No schema version changes.", "", "## Edits", "",
                f"`org.yaml`: `framework_version: {previous}` becomes `framework_version: {version}`.", "",
                f"`company/state.md`: frontmatter `framework_version: {previous}` becomes `framework_version: {version}`.", "",
                CHECK, "",
                f"- `framework_version: {version}` in `org.yaml` and in `company/state.md`.",
                "- `git status --short` shows only `org.yaml` and `company/state.md`.", ""]
        return "\n".join(out)

    if len(notes) == 1:
        out += [f"Version {version} has one change: {lower_first(notes[0]['what'])}.", ""]
        for paragraph in notes[0]["intro"]:
            out += [paragraph, ""]
    else:
        out += [f"Version {version} bundles {len(notes)} changes:", ""]
        for note in notes:
            out.append(f"- **{upper_first(note['what'])}.** {note['intro'][0]}")
        out.append("")
    for line in schema_lines(notes):
        out += [line, ""]
    out += [APPLY_PARAGRAPH, "", "## Version", "",
            f"`org.yaml`: `framework_version: {previous}` becomes `framework_version: {version}`.", "",
            f"`company/state.md`: frontmatter `framework_version: {previous}` becomes `framework_version: {version}`.", ""]

    for number, note in enumerate(notes, 1):
        out += [f"## {number}. {upper_first(note['what'])}", ""]
        if len(notes) > 1:
            for paragraph in note["intro"][1:]:
                out += [paragraph, ""]
        for heading, content in note["body"]:
            out += demote([heading] + content)
        while out and not out[-1].strip():
            out.pop()
        out += ["", f"{SUMMARY} {note['summary']}", ""]

    out += ["## Summary for the CEO", ""]
    for note in notes:
        out += [note["summary"], ""]
    out += [CHECK, "", f"- `framework_version: {version}` in `org.yaml` and in `company/state.md`."]
    seen = set()
    for note in notes:
        for check in note["checks"]:
            if check not in seen:
                seen.add(check)
                out.append(check)
    out.append("")
    return "\n".join(out)


def build_paragraph(previous, version, notes):
    name = f"{previous}-to-{version}.md"
    if not notes:
        return f"Version `{version}` has no hq changes. No schema changes. Migration: `{name}` (version bump only)."
    schemas = " ".join(schema_lines(notes))
    if len(notes) == 1:
        return (f"Version `{version}` has one change: {lower_first(notes[0]['what'])}. "
                f"{notes[0]['intro'][0]} {schemas} Migration: `{name}`.")
    parts = " ".join(f"{upper_first(note['what'])}: {note['intro'][0]}" for note in notes)
    return f"Version `{version}` bundles {len(notes)} changes. {parts} {schemas} Migration: `{name}`."


def add_to_readme(readme, paragraph):
    start = readme.index("## Current status")
    following = readme.find("\n## ", start + 1)
    if following == -1:
        return readme.rstrip("\n") + "\n\n" + paragraph + "\n"
    head = readme[:following].rstrip("\n")
    return head + "\n\n" + paragraph + "\n" + readme[following:]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print the result, write nothing")
    args = parser.parse_args()

    readme_path = MIGRATIONS / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    listed = ENTRY.findall(readme)
    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    if not listed:
        print("error: migrations/README.md lists no version")
        return 1
    if version in listed:
        print(f"note: version {version} is already listed in migrations/README.md; nothing to fold")
        return 0
    previous = max(listed, key=key)
    target = MIGRATIONS / f"{previous}-to-{version}.md"
    if target.exists():
        print(f"error: migrations/{target.name} exists but migrations/README.md has no entry for {version}; "
              "a person must finish it (add the paragraph, fold the notes)")
        return 1
    try:
        paths, notes = read_notes()
    except NoteError as error:
        print(f"error: {error}")
        return 1

    content = build_file(previous, version, notes)
    paragraph = build_paragraph(previous, version, notes)
    if args.dry_run:
        print(f"--- migrations/{target.name}\n{content}\n--- migrations/README.md, new paragraph\n{paragraph}")
    else:
        target.write_text(content, encoding="utf-8")
        readme_path.write_text(add_to_readme(readme, paragraph), encoding="utf-8")
        for path in paths:
            path.unlink()
    verb = "would fold" if args.dry_run else "folded"
    print(f"{verb} {len(notes)} note(s) into migrations/{target.name} ({previous} to {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
