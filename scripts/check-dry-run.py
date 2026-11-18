#!/usr/bin/env python3
"""Check the output of a setup dry run against the answers file it came from.

Usage: python3 scripts/check-dry-run.py <hq folder> <answers file>

The hq folder is the folder where `/ceo-of-agents:init-fleet <answers file> --dry-run`
ran. Checks: the answers file is valid; no `{{` is left in any file; org.yaml
parses and its purpose, level, id, name, languages, chief of staff name,
departments (ids, agents, sources, models), gates, repos, tracker, policy,
employer rules and policies repo match the answers; company/state.md has
`schema: state/1`; the expected files exist; no `.git` was created. Local check,
not part of CI. Prints one line per problem and a last line `verdict: ok` or
`verdict: N problem(s)`. Needs PyYAML.
"""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent / "ci"))
import check_setup_answers as sa  # noqa: E402

BASE_FILES = (
    "CLAUDE.md", "operating-model.md", "org.yaml", "company/state.md", "company/decision-queue.md",
    "company/vision.md", "company/strategy.md", "decisions/0001-setup.md", "decisions/README.md",
    "inbox/README.md", "initiatives/README.md", "metrics/README.md", "archive/README.md",
    ".gitignore", ".ignore", ".claude/agents/reader.md", ".claude/agents/worker.md",
)


class Report:
    def __init__(self):
        self.problems = []
        self.notes = []

    def problem(self, message):
        self.problems.append(message)
        print(f"problem: {message}")

    def note(self, message):
        self.notes.append(message)
        print(f"note: {message}")

    def expect(self, what, actual, expected):
        if actual != expected:
            self.problem(f"{what}: org.yaml has {actual!r}, the answers give {expected!r}")


def read_yaml(path, report, label):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        report.problem(f"{label} does not parse: {str(exc).splitlines()[0] if str(exc) else exc}")
        return None


def tier_lists(answers):
    """Final gate lists from the table of gates/default.md and the answers."""
    tiers = dict(sa.gate_tiers())
    gates = answers.get("gates")
    if isinstance(gates, dict):
        for key in ("stricter", "looser"):
            for action, tier in (gates.get(key) or {}).items():
                tiers[action] = tier
    return {tier: [a for a in tiers if tiers[a] == tier] for tier in sa.GATE_TIERS}, tiers


def expected_departments(answers, tiers_list):
    """List of expected org.yaml department items (id, agent, from_catalog, display_name, model, workers)."""
    catalog = sa.catalog_entries()
    display = answers["names"]["departments"]
    agents = answers["names"].get("agents") or {}
    models = answers["models"]
    overrides = models.get("overrides") or {}
    top = models.get("top_workers") or []
    result = []
    for dept in answers["departments"]:
        dept_id = dept["id"]
        item = {"id": dept_id, "display_name": display[dept_id]}
        if dept["from"] == "own":
            item.update(agent=dept["name"], from_catalog="own")
        else:
            role = catalog[dept_id]["role"] if dept["from"] == "catalog" else dept["role"]
            if dept_id in agents:
                agent = agents[dept_id]
            elif display[dept_id].strip().lower() == role.lower():
                agent = dept_id
            else:
                agent = sa.slug(display[dept_id])
            item.update(agent=agent, from_catalog=dept_id if dept["from"] == "catalog" else "custom")
            item["model"] = tiers_list[0] if dept_id in top else overrides.get(dept_id, models["departments"])
            if dept_id in top:
                item["workers"] = "same"
        if dept["from"] == "catalog" and "changes" in dept:
            item["adapted"] = True
        result.append(item)
    return result


def check_org_yaml(org, answers, report):
    purpose = answers["org"]["purpose"]
    level = answers["org"].get("level", "company")
    report.expect("org.purpose", (org.get("org") or {}).get("purpose"), purpose)
    report.expect("org.level", (org.get("org") or {}).get("level"), level)
    report.expect("org.id", (org.get("org") or {}).get("id"), answers["org"]["id"])
    report.expect("org.name", (org.get("org") or {}).get("name"), answers["org"]["name"])
    report.expect("language.chat", (org.get("language") or {}).get("chat"), answers["language"]["chat"])
    report.expect("language.files", (org.get("language") or {}).get("files"), answers["language"]["files"])
    report.expect("cos.display_name", (org.get("cos") or {}).get("display_name"), answers["names"]["cos"])
    ceo_name = answers["names"]["ceo"]
    report.expect("ceo.display_name", (org.get("ceo") or {}).get("display_name"), "" if ceo_name == "later" else ceo_name)
    profile = answers.get("ceo", {}).get("profile")
    org_ceo = org.get("ceo") or {}
    if "profile" not in org_ceo:
        if profile:
            report.note(f"ceo.profile is {profile!r} in the answers and org.yaml has no ceo.profile (the profile change may not be merged yet)")
    else:
        report.expect("ceo.profile", org_ceo.get("profile"), profile)
    models = org.get("models") or {}
    report.expect("models.cos", models.get("cos"), answers["models"]["cos"])
    report.expect("models.departments", models.get("departments"), answers["models"]["departments"])

    final, _ = tier_lists(answers)
    gates = org.get("gates") or {}
    for tier in sa.GATE_TIERS:
        report.expect(f"gates.{tier}", sorted(gates.get(tier) or []), sorted(final[tier]))

    tiers = models.get("tiers") or list(sa.TIERS)
    want = expected_departments(answers, tiers)
    got = org.get("departments")
    if not isinstance(got, list):
        if want:
            report.problem(f"departments: org.yaml has {got!r}, expected a list")
        got = []
    report.expect("department ids", [d.get("id") for d in got], [d["id"] for d in want])
    by_id = {d.get("id"): d for d in got if isinstance(d, dict)}
    for item in want:
        actual = by_id.get(item["id"])
        if actual is None:
            continue
        for key in ("agent", "from_catalog", "display_name", "model", "workers", "adapted"):
            if actual.get(key) != item.get(key):
                report.problem(f"departments[{item['id']}].{key}: org.yaml has {actual.get(key)!r}, the answers give {item.get(key)!r}")
        if actual.get("connectors") != []:
            report.problem(f"departments[{item['id']}].connectors: must be [] at setup")

    check_repos(org, answers, purpose, level, report)
    check_policy(org, answers, purpose, level, report)


def hq_slug(url):
    match = re.search(r"github\.com[:/]([A-Za-z0-9-]+/[A-Za-z0-9._-]+?)(?:\.git)?/?$", url or "")
    return match.group(1) if match else None


def check_repos(org, answers, purpose, level, report):
    repos = answers.get("repos")
    want = []
    if isinstance(repos, list):
        for repo in repos:
            item = {"slug": repo["slug"], "role": repo["role"], "visibility": repo["visibility"],
                    "issues_home": answers.get("issues_home") == repo["slug"], "protected": repo["protected"]}
            if repo["exists"] is False:
                item["planned"] = True
            want.append(item)
        if answers.get("issues_home") == "hq":
            slug = hq_slug(answers["remote"]["hq"])
            want.append({"slug": slug, "role": "hq", "visibility": "private", "issues_home": True, "protected": False})
    got = org.get("repos")
    if not isinstance(got, list):
        got = []
    if sorted(want, key=lambda r: str(r["slug"])) != sorted([r for r in got if isinstance(r, dict)], key=lambda r: str(r.get("slug"))):
        report.problem(f"repos: org.yaml has {got!r}, the answers give {want!r}")
    roadmap = answers.get("roadmap")
    if isinstance(roadmap, dict):
        parts = roadmap["url"].rstrip("/").split("/")
        tracker = {"kind": "github-project", "owner": parts[-3], "number": int(parts[-1]), "status_field": roadmap["status_field"]}
    else:
        tracker = "none"
    report.expect("tracker", org.get("tracker"), tracker)


def check_policy(org, answers, purpose, level, report):
    policy = answers.get("policy")
    want = {"repo": policy["repo"], "local": policy["local"], "pin": str(policy["pin"])} if isinstance(policy, dict) else None
    got = org.get("policy")
    if isinstance(got, dict) and "pin" in got:
        got = dict(got, pin=str(got["pin"]))
    report.expect("policy", got, want)
    rules = answers.get("employer_rules")
    report.expect("employer_rules", org.get("employer_rules"), rules if purpose == "job" and rules not in (None, "none", "later") else None)
    repo = answers.get("policies_repo")
    if level == "holding":
        remote = repo["remote"]
        want_repo = {"local": repo["path"], "remote": "" if remote in ("none", "later") else remote}
    else:
        want_repo = None
    report.expect("policies_repo", org.get("policies_repo"), want_repo)


def check_files(root, answers, org, report):
    wanted = list(BASE_FILES)
    if answers["org"].get("level") == "holding":
        wanted.append("portfolio.yaml")
    elif (root / "portfolio.yaml").exists():
        report.problem("portfolio.yaml exists but this org is not a holding")
    for item in (org or {}).get("departments") or []:
        if not isinstance(item, dict):
            continue
        wanted += [f"departments/{item.get('id')}/charter.md", f"departments/{item.get('id')}/README.md"]
        if item.get("from_catalog") != "own":
            wanted.append(f".claude/agents/{item.get('agent')}.md")
    for rel in wanted:
        if not (root / rel).is_file():
            report.problem(f"missing file: {rel}")
    if answers["org"].get("level") == "holding":
        for rel in ("policies-repo.dry-run/README.md", "policies-repo.dry-run/policy.yaml"):
            if not (root / rel).is_file():
                report.problem(f"missing file: {rel} (the policies repo of a dry run)")
    if (root / ".git").exists():
        report.problem(".git exists: a dry run never runs git init")
    if (root / "policies-repo.dry-run" / ".git").exists():
        report.problem("policies-repo.dry-run/.git exists: a dry run never runs git init")


def check_leftovers(root, report):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if "{{" in line:
                report.problem(f"{path.relative_to(root)}:{number}: `{{{{` left in the file")
                break


def check_state(root, report):
    path = root / "company" / "state.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or text.find("\n---", 3) == -1:
        report.problem("company/state.md has no frontmatter")
        return
    try:
        front = yaml.safe_load(text[4:text.find("\n---", 3)])
    except yaml.YAMLError:
        report.problem("company/state.md frontmatter does not parse")
        return
    if not isinstance(front, dict) or front.get("schema") != "state/1":
        report.problem("company/state.md frontmatter does not have `schema: state/1`")


def main(argv):
    if len(argv) != 3:
        print("usage: python3 scripts/check-dry-run.py <hq folder> <answers file>", file=sys.stderr)
        return 2
    root, answers_path = Path(argv[1]), Path(argv[2])
    if not root.is_dir():
        print(f"{root} is not a folder", file=sys.stderr)
        return 2
    report = Report()
    try:
        answers = sa.load(answers_path)
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read {answers_path}: {exc}", file=sys.stderr)
        return 2
    invalid = sa.Checker(answers, str(answers_path)).run()
    if invalid:
        for line in invalid:
            report.problem(f"answers file: {line}")
        print(f"verdict: {len(report.problems)} problem(s)")
        return 1
    check_leftovers(root, report)
    org = None
    if (root / "org.yaml").is_file():
        org = read_yaml(root / "org.yaml", report, "org.yaml")
    if isinstance(org, dict):
        check_org_yaml(org, answers, report)
    elif org is not None:
        report.problem("org.yaml is not a mapping")
    check_state(root, report)
    check_files(root, answers, org if isinstance(org, dict) else {}, report)
    print("verdict: ok" if not report.problems else f"verdict: {len(report.problems)} problem(s)")
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
