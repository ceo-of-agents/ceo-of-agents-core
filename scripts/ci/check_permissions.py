#!/usr/bin/env python3
"""Check the permission rules that gates/permissions.md derives from the gates.

The rule groups table in gates/permissions.md is the source. This script reads
it, generates the rules for fixture orgs, and checks:
- every action id in the table is a known action id of gates/default.md;
- every rule is in a known form (Bash, Edit, Read, Skill) with balanced parentheses;
- no rule that can be allowed has a wildcard that can carry a shell or an
  interpreter, a file write, a git option that runs a program or writes a file,
  or a gh write (section "Never allowed"): in the table (groups marked `allow`
  under "When free"), in every generated `allow` list (also for an org whose
  every action is free) and in the `allowed-tools` of every skill; and no
  retired rule is still in the table;
- no rule of a group that can reach an `ok` action ends up in `allow`, for any
  fixture, and no rule is in both `allow` and `ask`;
- the default and the stricter example orgs of the "Examples" section produce
  exactly the lists below;
- merging keeps every other key and every rule that is not of this file,
  removes the retired rules, and a second merge changes nothing.

Run with `--render <org.yaml> [<settings.json>]` to print the merged settings
file for an hq, without writing anything (used for dry runs).
Needs PyYAML.
"""
import copy
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "gates" / "permissions.md"
DEFAULT_GATES = ROOT / "gates" / "default.md"
TIERS = ["free", "notice", "ok"]
SKILL_RULE = "Skill(ceo-of-agents:*)"
RULE_FORM = re.compile(r"^(Bash|Edit|Read|Skill)\((.+)\)$")
HEADER = "| Group | Scope | Actions | When free | Rules |"
RETIRED_HEADING = "## Retired rules"
SKILLS = ROOT / "skills"

# Programs that run code given in their arguments, or run another command
# named in them. A Bash rule for one of them must be exact (no wildcard).
SHELLS = {
    "sh", "bash", "zsh", "dash", "ksh", "mksh", "fish", "csh", "tcsh", "pwsh", "powershell",
    "env", "exec", "eval", "command", "builtin", "source", ".", "xargs", "nohup", "sudo", "doas",
    "su", "time", "nice", "timeout", "watch", "script", "osascript",
    "node", "nodejs", "deno", "bun", "npx", "ruby", "irb", "perl", "php", "lua", "luajit",
    "tclsh", "wish", "awk", "gawk", "mawk", "nawk", "R", "Rscript", "julia", "uv", "uvx",
}
INTERPRETER = re.compile(r"^(python|pypy|pip)[0-9.]*$")
# Programs that write or delete files named in their arguments.
WRITERS = {"cp", "mv", "rm", "ln", "install", "dd", "tee", "rsync", "scp", "curl", "wget", "sed",
           "truncate", "chmod", "chown"}
# git subcommands that take none of -c, --output, --upload-pack, --receive-pack,
# --exec, --ext-diff, --textconv (checked against git 2.50). Any other git
# command gets exact rules only. `remote` is safe only as `remote add`.
SAFE_GIT = {"status", "add", "commit", "mv", "rm", "init", "ls-files", "check-ignore"}
# gh commands that only read; any other gh command with a wildcard can write.
# `gh auth status` is left out on purpose: an option of it prints the token.
GH_READ = {
    "issue": {"list", "view", "status"}, "pr": {"list", "view", "diff", "checks", "status"},
    "repo": {"view", "list"}, "release": {"list", "view"}, "run": {"list", "view"},
    "workflow": {"list", "view"}, "label": {"list"}, "search": None,
    "project": {"view", "list", "item-list", "field-list"},
}


def load_groups():
    groups = []
    lines = DOC.read_text(encoding="utf-8").splitlines()
    start = lines.index(HEADER)
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        name, scope, actions, when_free, rules = cells
        groups.append({
            "name": name,
            "scope": scope,
            "when_free": when_free,
            "actions": re.findall(r"`([a-z-]+)`", actions),
            "rules": re.findall(r"`([^`]+)`", rules),
        })
    return groups


def load_retired():
    """Rules listed under "Retired rules": bullets that start with a rule."""
    lines = DOC.read_text(encoding="utf-8").splitlines()
    start = lines.index(RETIRED_HEADING)
    retired = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        match = re.match(r"^- `([^`]+)`", line)
        if match:
            retired.append(match.group(1))
    return retired


def command_words(rule):
    """The words of a Bash rule's command, leading VAR=value assignments
    dropped and a trailing `:*` written as ` *`; None for another tool."""
    match = re.match(r"^Bash\((.*)\)$", rule)
    if not match:
        return None
    command = match.group(1).strip()
    if command.endswith(":*"):
        command = command[:-2] + " *"
    words = command.split()
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        words = words[1:]
    return words


def risk(rule):
    """Why the rule must never be allowed (section "Never allowed"), or None."""
    words = command_words(rule)
    if words is None or not any("*" in w for w in words):
        return None
    if not words or "*" in words[0]:
        return "wildcard in place of the command"
    name = words[0].rsplit("/", 1)[-1]
    if name in SHELLS or INTERPRETER.match(name):
        return "wildcard rule for a shell or an interpreter"
    if name in WRITERS:
        return "wildcard rule for a command that writes files"
    rest = words[1:]
    if name == "git":
        sub = rest[0] if rest else "*"
        if "*" in sub or sub.startswith("-"):
            return "git rule with a wildcard or an option before the subcommand"
        if sub == "remote" and len(rest) > 1 and rest[1] == "add":
            return None
        if sub not in SAFE_GIT:
            return f"git {sub} with a wildcard (only exact rules for it: its options can run a program or write a file)"
    if name == "gh":
        group = rest[0] if rest else "*"
        verb = rest[1] if len(rest) > 1 else "*"
        if group not in GH_READ:
            return f"gh {group} with a wildcard (not a read)"
        if GH_READ[group] is not None and verb not in GH_READ[group]:
            return f"gh {group} {verb} with a wildcard (not a read)"
    return None


def skill_rules():
    """(skill file, rule) for every Bash rule in a skill's allowed-tools."""
    out = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match:
            continue
        front = yaml.safe_load(match.group(1)) or {}
        tools = front.get("allowed-tools") or ""
        if isinstance(tools, list):
            tools = " ".join(tools)
        for rule in re.findall(r"Bash\([^)]*\)", tools):
            out.append((path.relative_to(ROOT).as_posix(), rule))
    return out


def known_actions():
    text = DEFAULT_GATES.read_text(encoding="utf-8")
    block = re.search(r"```yaml\ngates:\n(.*?)```", text, re.S).group(1)
    gates = yaml.safe_load("gates:\n" + block)["gates"]
    return {a for tier in TIERS for a in gates[tier]}


def tier_of(actions, gates):
    rank = 0
    for action in actions:
        for i, tier in enumerate(TIERS):
            if action in gates.get(tier, []):
                rank = max(rank, i)
    return TIERS[rank]


def general(rule):
    """The rule without its repo or tracker part."""
    rule = rule.replace(" -R <slug> *)", " *)")
    return rule.replace(" <number> --owner <owner> *)", " *)")


def per_repo(rule, slug):
    if slug.endswith("/*"):
        return rule.replace(" -R <slug> *)", f" -R {slug})")
    return rule.replace("<slug>", slug)


def generate(org, groups):
    gates = org["gates"]
    repos = [r for r in (org.get("repos") or []) if not r.get("planned")]
    tracker = org.get("tracker")
    allow, ask = [SKILL_RULE], []
    for g in groups:
        tier = tier_of(g["actions"], gates)
        allowed = tier == "free" and g["when_free"] == "allow"
        if g["scope"] == "hq":
            if allowed:
                allow += g["rules"]
            elif tier == "ok":
                ask += g["rules"]
        elif g["scope"] == "repo":
            if allowed:
                allow += [per_repo(r, x["slug"]) for x in repos if not x["protected"] for r in g["rules"]]
            elif tier == "ok":
                ask += [general(r) for r in g["rules"]]
            if tier != "ok":
                ask += [per_repo(r, x["slug"]) for x in repos if x["protected"] for r in g["rules"]]
        elif g["scope"] == "tracker":
            if isinstance(tracker, dict) and tracker.get("kind") == "github-project":
                if allowed:
                    allow += [r.replace("<number>", str(tracker["number"])).replace("<owner>", tracker["owner"]) for r in g["rules"]]
            if tier == "ok":
                ask += [general(r) for r in g["rules"]]
    deny = list((org.get("accounts") or {}).get("forbidden_connectors") or [])
    return dedupe(allow), dedupe(ask), dedupe(deny)


def dedupe(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def managed_patterns(groups, retired):
    pats = [re.escape(SKILL_RULE)] + [re.escape(r) for r in retired]
    for g in groups:
        for rule in g["rules"]:
            for form in {rule, general(rule)}:
                p = re.escape(form)
                p = p.replace(re.escape("<slug>") + r"\ \*", r"[A-Za-z0-9-]+/(?:[A-Za-z0-9._-]+\ \*|\*)")
                p = p.replace(re.escape("<number>"), r"\d+").replace(re.escape("<owner>"), r"[A-Za-z0-9-]+")
                pats.append(p)
    return re.compile("^(?:" + "|".join(pats) + ")$")


def merge(settings, org, groups, retired):
    allow, ask, deny = generate(org, groups)
    managed = managed_patterns(groups, retired)
    out = copy.deepcopy(settings)
    perms = out.setdefault("permissions", {})
    for key, new in (("allow", allow), ("ask", ask)):
        kept = [r for r in perms.get(key, []) if not managed.match(r) or r in new]
        kept += [r for r in new if r not in kept]
        if kept:
            perms[key] = kept
        else:
            perms.pop(key, None)
    if deny or perms.get("deny"):
        perms["deny"] = dedupe(perms.get("deny", []) + deny)
    return out


DEFAULT_ORG = {
    "gates": {
        "free": ["issues-and-labels", "comments", "drafts", "open-pr", "research", "hq-write"],
        "notice": ["push-non-deploy-branch", "hq-commit", "dispatch-pushing-department"],
        "ok": ["merge", "deploy", "publish", "contact-people", "spend-money", "rotate-secrets", "delete-data",
               "org-or-repo-settings", "change-brand-rules", "change-policy-rules", "file-or-sign", "make-payment"],
    },
    "accounts": {"forbidden_connectors": []},
    "repos": [
        {"slug": "acme/app", "role": "code", "visibility": "public", "issues_home": False, "protected": False},
        {"slug": "acme/hq", "role": "hq", "visibility": "private", "issues_home": True, "protected": False},
        {"slug": "partner/site", "role": "site", "visibility": "public", "issues_home": False, "protected": True},
    ],
    "tracker": {"kind": "github-project", "owner": "acme", "number": 3, "status_field": "Status"},
}

STRICT_ORG = copy.deepcopy(DEFAULT_ORG)
STRICT_ORG["gates"] = {
    "free": ["drafts", "open-pr", "hq-write"],
    "notice": ["push-non-deploy-branch", "hq-commit", "dispatch-pushing-department", "research"],
    "ok": DEFAULT_ORG["gates"]["ok"] + ["issues-and-labels", "comments"],
}


ALL_FREE_ORG = copy.deepcopy(DEFAULT_ORG)
ALL_FREE_ORG["gates"] = {"free": sorted({a for t in DEFAULT_ORG["gates"].values() for a in t}), "notice": [], "ok": []}


def expected(groups, names):
    return [r for g in groups if g["name"] in names for r in g["rules"]]


def repo_rules(groups, names, slugs):
    return [r.replace("<slug>", s) for g in groups if g["name"] in names for s in slugs for r in g["rules"]]


def check(groups, retired):
    errors = []
    actions = known_actions()
    table = {r for g in groups for r in g["rules"]}

    # The detector itself: these must be caught, and these must pass.
    for rule in ("Bash(sh *check-boot-set.sh*)", "Bash(bash -c *)", "Bash(python3 -c *)", "Bash(env *)",
                 "Bash(FOO=1 node *)", "Bash(sh:*)", "Bash(* --version)", "Bash(/usr/bin/zsh *)", "Bash(cp *)",
                 "Bash(git rev-list *)", "Bash(git -C * status *)", "Bash(git pull:*)", "Bash(git log *)",
                 "Bash(git diff:*)", "Bash(git push *)", "Bash(git *)", "Bash(git remote:*)",
                 "Bash(gh issue create -R acme/app *)", "Bash(gh issue comment:*)", "Bash(gh api *)",
                 "Bash(gh auth status *)", "Bash(gh project item-add 3 --owner acme *)", "Bash(gh pr merge *)"):
        if not risk(rule):
            errors.append(f"detector: does not flag {rule}")
    for rule in ("Bash(gh issue list *)", "Bash(git pull)", "Bash(sh /opt/tool/check.sh)", "Edit(/**)",
                 "Bash(shellcheck *)", "Bash(git rev-list --count HEAD)", "Bash(git commit *)", "Bash(git add:*)",
                 "Bash(git remote add *)", "Bash(git -C /x status)", "Bash(gh auth status)",
                 "Bash(gh search issues *)", "Bash(gh project item-list:*)", "Bash(mkdir *)"):
        if risk(rule):
            errors.append(f"detector: flags {rule}")

    if not retired:
        errors.append("gates/permissions.md: no rule under \"Retired rules\"")
    for rule in retired:
        if rule in table:
            errors.append(f"retired rule still in the table: {rule}")
    for g in groups:
        if g["when_free"] not in ("allow", "ask"):
            errors.append(f"group {g['name']}: \"When free\" is {g['when_free']!r}, not allow or ask")
        elif g["when_free"] == "allow":
            for rule in g["rules"]:
                why = risk(rule)
                if why:
                    errors.append(f"group {g['name']} is marked allow but has a rule that is never allowed ({why}): {rule}")
    for path, rule in skill_rules():
        why = risk(rule)
        if why:
            errors.append(f"{path}: allowed-tools: {why}: {rule}")
    for g in groups:
        for a in g["actions"]:
            if a not in actions:
                errors.append(f"group {g['name']}: unknown action id {a}")
        if g["scope"] not in ("hq", "repo", "tracker"):
            errors.append(f"group {g['name']}: unknown scope {g['scope']}")
        for r in g["rules"]:
            if not RULE_FORM.match(r) or r.count("(") != r.count(")"):
                errors.append(f"group {g['name']}: rule not in a known form: {r}")
            if g["scope"] == "repo" and " -R <slug> *)" not in r:
                errors.append(f"group {g['name']}: repo rule without ' -R <slug> *': {r}")

    ok_groups = {g["name"] for g in groups if tier_of(g["actions"], DEFAULT_ORG["gates"]) == "ok"}
    if not {"push", "merge", "release", "settings", "secrets", "delete", "github-api"} <= ok_groups:
        errors.append("default table: an ask group is not ok-tier: " + ", ".join(sorted(ok_groups)))

    for label, org in (("default", DEFAULT_ORG), ("strict", STRICT_ORG), ("all-free", ALL_FREE_ORG)):
        allow, ask, _ = generate(org, groups)
        both = set(allow) & set(ask)
        if both:
            errors.append(f"{label}: rules in both allow and ask: {sorted(both)}")
        for rule in allow:
            why = risk(rule)
            if why:
                errors.append(f"{label}: allow has a rule that is never allowed ({why}): {rule}")
        for g in groups:
            if tier_of(g["actions"], org["gates"]) == "ok":
                leaked = [r for r in allow if r in g["rules"] or r.startswith(general(g["rules"][0])[:-2])]
                if leaked:
                    errors.append(f"{label}: ok-tier group {g['name']} in allow: {leaked}")

    # Default example
    allow, ask, deny = generate(DEFAULT_ORG, groups)
    want_allow = [SKILL_RULE] + expected(groups, {"read-github", "sync-hq", "plugin-files", "edit-hq"})
    want_ask = (repo_rules(groups, {"issues", "comments", "pull-requests"}, ["partner/site"])
                + expected(groups, {"push", "merge", "release", "settings", "secrets", "delete", "github-api"}))
    if sorted(allow) != sorted(want_allow):
        errors.append(f"default example allow differs: extra {sorted(set(allow) - set(want_allow))}, missing {sorted(set(want_allow) - set(allow))}")
    if sorted(ask) != sorted(want_ask):
        errors.append(f"default example ask differs: extra {sorted(set(ask) - set(want_ask))}, missing {sorted(set(want_ask) - set(ask))}")
    if deny:
        errors.append(f"default example deny not empty: {deny}")
    if any(r in allow for r in expected(groups, {"commit-hq"})) or any(r in ask for r in expected(groups, {"commit-hq"})):
        errors.append("default example: commit-hq (notice) has a rule")

    # Strict example
    allow, ask, _ = generate(STRICT_ORG, groups)
    want_allow = [SKILL_RULE, "Edit(/**)"]
    want_ask = (expected(groups, {"push", "merge", "release", "settings", "secrets", "delete", "github-api"})
                + [general(r) for r in expected(groups, {"issues", "comments", "tracker"})]
                + ["Bash(gh pr create -R partner/site *)"])
    if sorted(allow) != sorted(want_allow):
        errors.append(f"strict example allow differs: extra {sorted(set(allow) - set(want_allow))}, missing {sorted(set(want_allow) - set(allow))}")
    if sorted(ask) != sorted(want_ask):
        errors.append(f"strict example ask differs: extra {sorted(set(ask) - set(want_ask))}, missing {sorted(set(want_ask) - set(ask))}")
    if "Bash(gh issue create *)" not in ask:
        errors.append("strict example: gh issue create is not asked")

    # Merge: keeps other keys and own rules, idempotent, tightens on regeneration
    before = {
        "enabledPlugins": {"ceo-of-agents@ceo-of-agents": True},
        "attribution": {"commit": "", "pr": ""},
        "permissions": {"allow": ["Bash(make test)", SKILL_RULE, "Bash(gh issue create -R old/repo *)",
                                  "Bash(gh issue create -R acme/app *)", "Bash(gh project item-add 3 --owner acme *)"]
                                 + retired,
                        "ask": list(retired),
                        "deny": ["mcp__other"], "defaultMode": "default"},
    }
    org = copy.deepcopy(DEFAULT_ORG)
    org["accounts"]["forbidden_connectors"] = ["mcp__work"]
    once = merge(before, org, groups, retired)
    twice = merge(once, org, groups, retired)
    if once != twice:
        errors.append("merge is not idempotent")
    for key in ("enabledPlugins", "attribution"):
        if once.get(key) != before[key]:
            errors.append(f"merge changed {key}")
    p = once["permissions"]
    if p.get("defaultMode") != "default":
        errors.append("merge dropped permissions.defaultMode")
    if "Bash(make test)" not in p["allow"]:
        errors.append("merge dropped an own allow rule")
    if "Bash(gh issue create -R old/repo *)" in p["allow"]:
        errors.append("merge kept a managed rule for an unregistered repo")
    if "Bash(gh issue create -R acme/app *)" in p["allow"] or "Bash(gh project item-add 3 --owner acme *)" in p["allow"]:
        errors.append("merge kept a 0.15.0 allow rule for a GitHub write")
    left = [r for r in p.get("allow", []) + p.get("ask", []) if r in retired]
    if left:
        errors.append(f"merge kept retired rules: {left}")
    if p["allow"].count(SKILL_RULE) != 1:
        errors.append("merge: Skill rule not exactly once")
    if p["deny"] != ["mcp__other", "mcp__work"]:
        errors.append(f"merge deny wrong: {p['deny']}")
    freed = copy.deepcopy(org)
    freed["repos"][2]["protected"] = False
    after = merge(once, freed, groups, retired)
    if "Bash(gh issue comment -R partner/site *)" in after["permissions"].get("ask", []) or \
            "Bash(gh issue comment -R partner/site *)" in after["permissions"].get("allow", []):
        errors.append("regeneration after freeing a repo kept its ask rules or allowed them")
    strict_after = merge(once, dict(org, gates=STRICT_ORG["gates"]), groups, retired)
    if any(r.startswith("Bash(gh issue create -R") for r in strict_after["permissions"]["allow"]):
        errors.append("regeneration to a stricter org kept gh issue create in allow")
    return errors


def main(argv):
    groups = load_groups()
    retired = load_retired()
    if len(argv) >= 2 and argv[0] == "--render":
        org = yaml.safe_load(Path(argv[1]).read_text(encoding="utf-8"))
        settings = json.loads(Path(argv[2]).read_text(encoding="utf-8")) if len(argv) > 2 and Path(argv[2]).exists() else {}
        print(json.dumps(merge(settings, org, groups, retired), indent=2, ensure_ascii=False))
        return 0
    errors = check(groups, retired)
    for error in errors:
        print(f"error: {error}")
    print(f"{len(groups)} rule groups, {sum(len(g['rules']) for g in groups)} rules, {len(retired)} retired; "
          f"{len(skill_rules())} skill Bash rules scanned; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
