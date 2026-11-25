#!/usr/bin/env python3
"""Check scripts/check-boot-set.sh against schemas/boot-set.md.

Rules:
- The budgets table in schemas/boot-set.md and the block between
  "# BUDGETS BEGIN" and "# BUDGETS END" in the script name the same files with
  the same byte budgets, and each row's KiB figure times 1024 equals its bytes.
- The initiative page budget in schemas/boot-set.md ("at most N KiB per page
  (B bytes") and STATUS_BUDGET in the script are the same number, and the
  script reports pages over it and their long lines (nothing without pages).
- The script behaves as documented on small fixture hqs (budgets, long lines in
  characters, pending line groups including parent and child items, missing
  files, exit codes, and the line format of the optional company/todo.md,
  silent when that file is missing).
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "boot-set.md"
SCRIPT = ROOT / "scripts" / "check-boot-set.sh"
ROW = re.compile(r"^\|\s*(`[^`]+`|Whole boot set)\s*\|\s*(\d+) KiB \(([\d,]+) bytes\)\s*\|")


def schema_budgets(errors):
    budgets = {}
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        name, kib, raw = match.groups()
        name = "TOTAL" if name == "Whole boot set" else name.strip("`")
        value = int(raw.replace(",", ""))
        if int(kib) * 1024 != value:
            errors.append(f"schemas/boot-set.md: {name}: {kib} KiB is not {value} bytes")
        budgets[name] = value
    return budgets


def script_budgets(errors):
    text = SCRIPT.read_text(encoding="utf-8")
    block = re.search(r"# BUDGETS BEGIN\n(.*?)# BUDGETS END", text, re.DOTALL)
    if not block:
        errors.append("scripts/check-boot-set.sh: no # BUDGETS BEGIN / # BUDGETS END block")
        return {}
    budgets = {}
    for match in re.finditer(r"([\w./-]+) (\d+)", block.group(1)):
        budgets[match.group(1)] = int(match.group(2))
    return budgets


PAGE = re.compile(r"at most (\d+) KiB per page \(([\d,]+) bytes")


def page_budgets(errors):
    schema = PAGE.search(SCHEMA.read_text(encoding="utf-8"))
    script = re.search(r"^STATUS_BUDGET=(\d+)$", SCRIPT.read_text(encoding="utf-8"), re.MULTILINE)
    if not schema:
        errors.append("schemas/boot-set.md: no initiative page budget (\"at most N KiB per page (B bytes\")")
    if not script:
        errors.append("scripts/check-boot-set.sh: no STATUS_BUDGET=<bytes> line")
    if not schema or not script:
        return
    kib, raw = int(schema.group(1)), int(schema.group(2).replace(",", ""))
    if kib * 1024 != raw:
        errors.append(f"schemas/boot-set.md: initiative page budget {kib} KiB is not {raw} bytes")
    if raw != int(script.group(1)):
        errors.append(f"initiative page budget: schemas/boot-set.md has {raw}, scripts/check-boot-set.sh has {script.group(1)}")


def pages(errors):
    page = "---\ninitiative: beta\nstate: active\n---\n\n# Beta\n\n## State\nOn track.\n"
    cases = [
        ("no initiative pages", {"initiatives/README.md": "# Initiatives\n"}, ["verdict: ok"],
         ["initiative pages", "initiative page lines"]),
        ("small initiative page", {"initiatives/beta/status.md": page},
         ["initiative pages over 4096 bytes: 0", "initiative page lines over 300 characters: 0", "verdict: ok"], []),
        ("big initiative page", {"initiatives/beta/status.md": page + ("w" * 200 + "\n") * 25},
         ["initiative pages over 4096 bytes: 1", "initiatives/beta/status.md: ", " bytes, over by ", "verdict: 1 issue(s)"], []),
        ("long page lines", {"initiatives/beta/status.md": page + "é" * 301 + "\n" + "é" * 300 + "\n",
                             "initiatives/gamma/status.md": page + ("x" * 400 + "\n") * 4},
         ["initiative pages over 4096 bytes: 0", "initiative page lines over 300 characters: 5",
          "initiatives/beta/status.md line 10 (301 characters)", "and 2 more", "verdict: 5 issue(s)"], []),
    ]
    for label, extra, present, absent in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build(root, hq(**extra))
            got, out = run(root)
        if got != 0:
            errors.append(f"{label}: exit {got}, expected 0")
        errors.extend(f"{label}: output lacks {n!r}" for n in present if n not in out)
        errors.extend(f"{label}: output has {n!r}" for n in absent if n in out)


def run(target):
    proc = subprocess.run(["sh", str(SCRIPT), str(target)], capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout


def build(root, files):
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))


GOOD_STATE = (
    "---\nlast_updated: 2026-01-01\n---\n# State\n\n## Waiting on the CEO\n"
    "- ACME-A1 [high] {ok}: Approve the listing\n"
    "- ACME-A2 [low] {do}: Rename the folder\n"
    "- ACME-D1 [normal] {decide}: Pick a name\n\n## Open decisions\n- none\n"
)


def hq(state=GOOD_STATE, **extra):
    files = {"CLAUDE.md": "x\n", "org.yaml": "a: 1\n", "company/vision.md": "v\n",
             "company/strategy.md": "s\n", "company/state.md": state,
             "company/decision-queue.md": "q\n", "accounts.local.yaml": "p: 1\n"}
    files.update(extra)
    return files


GOOD_TODO = (
    "---\nschema: todo/1\nlast_updated: 2026-01-15\nnext_todo: 5\n---\n\n# CEO todo list\n\n## Open\n"
    "- ACME-T3 [high]: Review the vendor contract. Status: waiting on Legal (since 2026-01-10)\n"
    "- ACME-T4 [normal]: Reply to the beta tester (since 2026-01-14)\n\n"
    "## Done (last 7 days)\n- ACME-T2 [low]: Renew the domain (done 2026-01-12)\n"
)


TAGGED_TODO = (
    "---\nschema: todo/1\nlast_updated: 2026-01-15\nnext_todo: 8\ncategories: [admin, team]\n---\n\n# CEO todo list\n\n## Open\n"
    "- ACME-T3 [high]: Review the vendor contract #admin. Status: waiting on Legal (since 2026-01-10)\n"
    "  - ACME-T6 [low]: Check the export #team (since 2026-01-14)\n"
    "- ACME-T4 [normal]: Reply to the beta tester (since 2026-01-14)\n\n"
    "## Done (last 7 days)\n- ACME-T2 [low]: Renew the domain #admin (done 2026-01-12)\n"
)


def pending(*lines):
    return "## Waiting on the CEO\n" + "".join(line + "\n" for line in lines) + "\n## Next\n"


def behaviour(errors):
    def case(label, files, checks, code=0, absent=()):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build(root, files)
            got, out = run(root)
        if got != code:
            errors.append(f"{label}: exit {got}, expected {code}")
        for needle in checks:
            if needle not in out:
                errors.append(f"{label}: output lacks {needle!r}")
        for needle in absent:
            if needle in out:
                errors.append(f"{label}: output has {needle!r}")

    case("clean hq", hq(), ["verdict: ok", "pending lines not in the line format: 0"], absent=["company/todo.md"])
    case("good todo list", hq(**{"company/todo.md": GOOD_TODO}),
         ["company/todo.md lines not in the line format: 0", "verdict: ok"])
    case("tagged todo list", hq(**{"company/todo.md": TAGGED_TODO}),
         ["company/todo.md lines not in the line format: 0", "verdict: ok"])
    case("empty todo list", hq(**{"company/todo.md": "## Open\n- none\n\n## Done (last 7 days)\n- none\n"}),
         ["company/todo.md lines not in the line format: 0", "verdict: ok"])
    case("bad todo lines", hq(**{"company/todo.md": GOOD_TODO.replace("## Done", "- ACME-T5: no urgency (since 2026-01-14)\n"
                                                                  "- ACME-A6 [low]: an A code (since 2026-01-14)\n\n## Done")
                                 + "- ACME-T7 [low]: still open (since 2026-01-12)\n"}),
         ["company/todo.md lines not in the line format: 3", "line 13: - ACME-T5: no urgency", "verdict: 3 issue(s)"])
    case("at budget", hq(**{"org.yaml": "a" * 6144}), ["org.yaml: 6144 bytes, budget 6144: ok"])
    case("one byte over", hq(**{"org.yaml": "a" * 6145}), ["over by 1 bytes", "verdict: 1 issue(s)"])
    case("300 characters", hq(state=GOOD_STATE + "é" * 300 + "\n"), ["lines over 300 characters: 0"])
    case("301 characters", hq(state=GOOD_STATE + "é" * 301 + "\n"), ["lines over 300 characters: 1", "(301 characters)"])
    case("untagged A line", hq(state=pending("- ACME-A2 [high]: Approve the store listing")),
         ["pending lines without a kind: 1", "pending lines whose kind does not fit the code: 0", "pending lines not in the line format: 0"])
    case("A with decide", hq(state=pending("- ACME-A2 [high] {decide}: Approve it")),
         ["pending lines without a kind: 0", "pending lines whose kind does not fit the code: 1", "pending lines not in the line format: 0"])
    case("junk line", hq(state=pending("- just something")),
         ["pending lines without a kind: 0", "pending lines whose kind does not fit the code: 0", "pending lines not in the line format: 1"])
    nested0 = ["pending lines nested wrongly: 0", "verdict: ok"]
    case("parents and children", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch the beta once the items below are done (since 2026-01-12)",
        "  - ACME-A8 [normal] {ok}: approve the store copy (since 2026-01-12)",
        "  - ACME-D5 [normal] {decide}: decide the beta price, see decision queue (since 2026-01-13)",
        "- ACME-D3 [normal] {wait}: pricing model decided (decision 0012); follow-ups below (since 2026-01-10)",
        "  - ACME-A9 [low] {do}: update the price in the console (since 2026-01-15)",
        "- ACME-A10 [low] {do}: a single item")), nested0)
    case("wait on an A parent", hq(state=pending(
        "- ACME-A7 [high] {wait}: approved 2026-01-14, runs when the items below are done (since 2026-01-12)",
        "  - ACME-A8 [normal] {do}: rename the folder (since 2026-01-12)")), nested0)
    case("orphan child", hq(state=pending("  - ACME-A8 [normal] {ok}: approve it (since 2026-01-12)")),
         ["pending lines nested wrongly: 1", "pending lines not in the line format: 0", "verdict: 1 issue(s)"])
    case("child after none", hq(state=pending("- none", "  - ACME-A8 [normal] {ok}: approve it")),
         ["pending lines nested wrongly: 1", "verdict: 1 issue(s)"])
    case("grandchild", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch",
        "  - ACME-A8 [normal] {ok}: approve the copy",
        "    - ACME-A9 [low] {do}: sub-step")),
         ["pending lines nested wrongly: 1", "pending lines not in the line format: 0", "verdict: 1 issue(s)"])
    case("bad indent", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch", "   - ACME-A8 [normal] {ok}: three spaces", "\t- ACME-A9 [low] {do}: tab")),
         ["pending lines nested wrongly: 2", "verdict: 2 issue(s)"])
    case("wait without child", hq(state=pending(
        "- ACME-D3 [normal] {wait}: decided (decision 0012)",
        "- ACME-A2 [low] {do}: Rename the folder")),
         ["pending lines nested wrongly: 1", "line 2: - ACME-D3 [normal] {wait}: decided", "verdict: 1 issue(s)"])
    case("wait as last line", hq(state="## Waiting on the CEO\n- ACME-D3 [normal] {wait}: decided (decision 0012)\n"),
         ["pending lines nested wrongly: 1", "verdict: 1 issue(s)"])
    case("wait on a child", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch", "  - ACME-A8 [normal] {wait}: grouped")),
         ["pending lines nested wrongly: 1", "pending lines whose kind does not fit the code: 0",
          "pending lines not in the line format: 0", "verdict: 1 issue(s)"])
    case("wait in a child's text", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch", "  - ACME-A8 [normal] {ok}: approve the {wait} label")),
         ["pending lines nested wrongly: 0", "verdict: ok"])
    case("child without a kind", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch", "  - ACME-A8 [normal]: approve the copy")),
         ["pending lines without a kind: 1", "pending lines nested wrongly: 0", "verdict: 1 issue(s)"])
    case("child with a wrong kind", hq(state=pending(
        "- ACME-A7 [high] {ok}: launch", "  - ACME-A8 [normal] {decide}: approve the copy")),
         ["pending lines whose kind does not fit the code: 1", "pending lines nested wrongly: 0"])
    case("todo with a child", hq(**{"company/todo.md": GOOD_TODO.replace(
        "\n- ACME-T4", "\n  - ACME-T6 [low]: Check the export (since 2026-01-14)\n- ACME-T4")}),
         ["company/todo.md lines not in the line format: 0", "verdict: ok"])
    case("todo bad children", hq(**{"company/todo.md": GOOD_TODO.replace(
        "## Open\n", "## Open\n  - ACME-T6 [low]: Orphan (since 2026-01-14)\n").replace(
        "(done 2026-01-12)\n", "(done 2026-01-12)\n  - ACME-T7 [low]: Done child (done 2026-01-12)\n")}),
         ["company/todo.md lines not in the line format: 2", "verdict: 2 issue(s)"])
    case("many long lines", hq(state=GOOD_STATE + ("w" * 301 + "\n") * 5),
         ["lines over 300 characters: 5", "and 2 more"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        files = hq()
        del files["accounts.local.yaml"]
        build(root, files)
        _, out = run(root)
        if "accounts.local.yaml: missing, counted as 0 bytes" not in out:
            errors.append("missing file: not reported as missing, counted as 0 bytes")
        got, _ = run(root / "nope")
        if got != 2:
            errors.append(f"non-directory argument: exit {got}, expected 2")


def main():
    errors = []
    schema = schema_budgets(errors)
    script = script_budgets(errors)
    if schema != script:
        for name in sorted(set(schema) | set(script)):
            if schema.get(name) != script.get(name):
                errors.append(f"budget {name}: schemas/boot-set.md has {schema.get(name)}, scripts/check-boot-set.sh has {script.get(name)}")
    if not schema:
        errors.append("schemas/boot-set.md: no budgets table rows found")
    behaviour(errors)
    page_budgets(errors)
    pages(errors)
    for error in errors:
        print(f"error: {error}")
    print(f"{len(schema)} budgets in the schema; {len(script)} in the script; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
