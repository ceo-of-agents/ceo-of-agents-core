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
  every action is free) and in the `allowed-tools` of every skill; the two
  guarded wildcards (`gh api *`, `gh pr merge -R <exact slug> *`) are the only
  exceptions, and only while all their guards are in the generated `ask`; and
  no retired rule is still in the table;
- the tier mapping: free and notice put a group marked `allow` in `allow`, ok
  puts it in `ask`, a group marked `ask` never reaches `allow`, a protected
  repo's rules ask, and `guard` and `deny` groups do not depend on the tier;
- no rule of a group that can reach an `ok` action ends up in `allow`, for any
  fixture, no rule is in both `allow` and `ask`, and no generated `allow` rule
  matches a `deny` rule;
- the push-current rules are exact (no wildcard);
- the deny baseline is in every generated `deny`; real command spellings are
  refused, asked or allowed as the section "Never, in any mode" says;
- the default, merge-notice, stricter and all-free example orgs produce
  exactly the lists of the "Examples" section;
- merging keeps every other key and every rule that is not of this file,
  removes the retired rules, adds the baseline, and a second merge changes
  nothing.

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
    """Every row of every table that has the group header, in file order."""
    groups = []
    lines = DOC.read_text(encoding="utf-8").splitlines()
    for start, header in enumerate(lines):
        if header != HEADER:
            continue
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


# Guarded wildcards (section "Never allowed"): the only allow rules with a
# wildcard that may carry a gh write, and only with every guard in `ask`.
API_GUARDS = ["Bash(gh api *-X*)", "Bash(gh api *--method*)", "Bash(gh api -f*)", "Bash(gh api * -f*)",
              "Bash(gh api -F*)", "Bash(gh api * -F*)", "Bash(gh api *--field*)", "Bash(gh api *--raw-field*)",
              "Bash(gh api *--input*)"]
MERGE_GUARDS = ["Bash(gh pr merge *--admin*)", "Bash(gh pr merge * -R*)", "Bash(gh pr merge *--repo*)",
                "Bash(gh pr merge *://*)"]
API_ALLOW = "Bash(gh api *)"
MERGE_ALLOW = re.compile(r"^Bash\(gh pr merge -R [A-Za-z0-9-]+/[A-Za-z0-9._-]+ \*\)$")
MERGE_ALLOW_TABLE = "Bash(gh pr merge -R <slug> *)"


def guards_of(rule):
    """The guards a guarded wildcard needs in `ask`, or None for any other rule."""
    if rule == API_ALLOW:
        return API_GUARDS
    if MERGE_ALLOW.match(rule) or rule == MERGE_ALLOW_TABLE:
        return MERGE_GUARDS
    return None


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


def risk(rule, guarded_ok=False):
    """Why the rule must never be allowed (section "Never allowed"), or None.
    With guarded_ok, the two guarded wildcards pass (the caller checks their guards)."""
    if guarded_ok and guards_of(rule):
        return None
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


def rule_regex(rule):
    """Regex for the command text a Bash rule matches: `*` is any text; a
    trailing ` *` also matches the bare command."""
    match = re.match(r"^Bash\((.*)\)$", rule)
    inner = match.group(1)
    tail = ""
    if inner.endswith(" *"):
        inner, tail = inner[:-2], "(?: .*)?"
    return re.compile("^" + ".*".join(re.escape(p) for p in inner.split("*")) + tail + "$", re.S)


def matches(rule, command):
    return rule.startswith("Bash(") and bool(rule_regex(rule).match(command))


def verdict(command, allow, ask, deny):
    """What Claude Code does with a command: deny, then ask, then allow, else its own default."""
    for name, rules in (("deny", deny), ("ask", ask), ("allow", allow)):
        if any(matches(r, command) for r in rules):
            return name
    return "default"


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


def has_protected(org):
    """True when `repos:` has any entry with `protected: true` (exact repo, owner pattern or
    planned). An unregistered repo also counts as protected in the gates, but does not
    trigger this: a rule cannot know about repos the org has not listed."""
    return any(r.get("protected") is True for r in (org.get("repos") or []))


def hq_target(g, org, tier):
    """Where the rules of an hq group go: "allow", "ask" or None (nowhere)."""
    # A push cannot be told apart by repo, so an org with a protected repo is asked on every push.
    if g["name"] == "push-current" and has_protected(org):
        return "ask"
    if g["when_free"] == "allow" and tier in ("free", "notice"):
        return "allow"
    return "ask" if tier == "ok" else None


def group_rules(g, org):
    """(allow, ask, deny) rules of one group for an org: the tier mapping."""
    tier = tier_of(g["actions"], org["gates"])
    mode = g["when_free"]
    repos = [r for r in (org.get("repos") or []) if not r.get("planned")]
    tracker = org.get("tracker")
    if mode == "deny":
        return [], [], list(g["rules"])
    if mode == "guard":
        return [], list(g["rules"]), []
    if mode.startswith("guard if "):
        dep = next(x for x in GROUPS_FOR_DEP if x["name"] == mode[len("guard if "):])
        return [], (list(g["rules"]) if group_rules(dep, org)[0] else []), []
    allowed = mode == "allow" and tier in ("free", "notice")
    allow, ask = [], []
    if g["scope"] == "hq":
        target = hq_target(g, org, tier)
        if target == "allow":
            allow += g["rules"]
        elif target == "ask":
            ask += g["rules"]
    elif g["scope"] == "repo":
        if allowed:
            # an owner pattern is never allowed: only exact slugs
            allow += [per_repo(r, x["slug"]) for x in repos
                      if not x["protected"] and not x["slug"].endswith("/*") for r in g["rules"]]
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
    return allow, ask, []


GROUPS_FOR_DEP = []


def generate(org, groups):
    GROUPS_FOR_DEP[:] = groups
    allow, ask, deny = [SKILL_RULE], [], []
    for g in groups:
        a, k, d = group_rules(g, org)
        allow += a
        ask += k
        deny += d
    deny += list((org.get("accounts") or {}).get("forbidden_connectors") or [])
    return dedupe(allow), dedupe(ask), dedupe(deny)


def dedupe(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


# Retired rules that are removed from `ask` only: in `allow` or `deny` they may
# be the user's own rules, so the merge leaves them and the CEO is warned.
ASK_ONLY_RETIRED = ["Bash(git push *)"]


def managed_patterns(groups, retired, key="ask"):
    pats = [re.escape(SKILL_RULE)] + [re.escape(r) for r in retired if key == "ask" or r not in ASK_ONLY_RETIRED]
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
    out = copy.deepcopy(settings)
    perms = out.setdefault("permissions", {})
    for key, new in (("allow", allow), ("ask", ask), ("deny", deny)):
        # a forbidden connector in deny is only ever added, never removed
        managed = managed_patterns(groups, retired, key)
        kept = [r for r in perms.get(key, []) if not managed.match(r) or r in new]
        kept += [r for r in new if r not in kept]
        if kept:
            perms[key] = kept
        else:
            perms.pop(key, None)
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

MERGE_NOTICE_ORG = copy.deepcopy(DEFAULT_ORG)
MERGE_NOTICE_ORG["gates"]["notice"] = DEFAULT_ORG["gates"]["notice"] + ["merge"]
MERGE_NOTICE_ORG["gates"]["ok"] = [a for a in DEFAULT_ORG["gates"]["ok"] if a != "merge"]

STRICT_ORG = copy.deepcopy(DEFAULT_ORG)
STRICT_ORG["gates"] = {
    "free": ["drafts", "open-pr", "hq-write"],
    "notice": ["dispatch-pushing-department", "research"],
    "ok": DEFAULT_ORG["gates"]["ok"] + ["issues-and-labels", "comments", "push-non-deploy-branch", "hq-commit"],
}

# The default table with no protected repo: the only example where push-current is in allow.
OWN_REPOS_ORG = copy.deepcopy(DEFAULT_ORG)
OWN_REPOS_ORG["repos"] = [r for r in DEFAULT_ORG["repos"] if not r["protected"]]

ALL_FREE_ORG = copy.deepcopy(DEFAULT_ORG)
ALL_FREE_ORG["gates"] = {"free": sorted({a for t in DEFAULT_ORG["gates"].values() for a in t}), "notice": [], "ok": []}

ORGS = (("default", DEFAULT_ORG), ("own-repos", OWN_REPOS_ORG), ("merge-notice", MERGE_NOTICE_ORG), ("strict", STRICT_ORG), ("all-free", ALL_FREE_ORG))

PUSH_CURRENT = ["Bash(git push origin HEAD)", "Bash(git push -u origin HEAD)"]
RESET_ASK = ["Bash(git reset --hard*)", "Bash(git reset * --hard*)"]

# Real spellings, and what Claude Code must do with each (deny > ask > allow).
DENY_COMMANDS = [
    "git push --force", "git push origin main --force", "git push --force-with-lease origin main",
    "git push --force-if-includes", "git push -f", "git push origin -f", "git push origin main -f",
    "git push origin +main", "git push --delete origin x", "git push origin --delete x", "git push -d origin x",
    "git push origin -d x", "git push origin :x", "git push --mirror", "git push origin --prune",
    "git -C repo push --force", "git -c a=b push -f origin x", "git -C repo push origin --delete x",
    "git push origin ':x'", 'git push origin ":x"',
    "git filter-branch --tree-filter x", "git filter-repo --path x", "git reflog expire --all",
    "git reflog delete HEAD@{1}", "git clean -fdx", "git clean -f", "git clean -n -fd", "git clean --force",
    "gh repo delete acme/app --yes", "gh release delete v1", "gh release delete-asset v1 a.zip",
    "gh api -X DELETE repos/a/b", "gh api repos/a/b -XDELETE", "gh api repos/a/b --method DELETE",
    "gh api repos/a/b --method=DELETE", "gh api -X delete repos/a/b", "gh api repos/a/b --method=delete",
]
RESET_COMMANDS = ["git reset --hard", "git reset --hard HEAD~1", "git reset HEAD~1 --hard"]
PUSH_OK_COMMANDS = ["git push -u origin HEAD", "git push origin HEAD"]
# No rule at all: Claude Code's own prompt (never allow, never deny).
PUSH_DEFAULT_COMMANDS = ["git push", "git push origin", "git push -u origin feature", "git push origin main"]
API_READ_COMMANDS = ["gh api repos/acme/app/pulls/3", "gh api /user --jq .login", "gh api repos/acme/app/issues --paginate"]
API_WRITE_COMMANDS = [
    "gh api -X POST repos/a/b/issues", "gh api repos/a/b -X PATCH", "gh api repos/a/b -XPUT",
    "gh api repos/a/b --method PUT", "gh api repos/a/b --method=POST", "gh api repos/a/b -f title=x",
    "gh api -f title=x repos/a/b", "gh api repos/a/b -F a=b", "gh api -F a=b repos/a/b",
    "gh api repos/a/b --field a=b", "gh api repos/a/b --raw-field a=b", "gh api repos/a/b --input f.json",
    "gh api graphql -f query=x",
]
MERGE_ALLOWED_COMMANDS = ["gh pr merge -R acme/app 12 --squash --delete-branch", "gh pr merge -R acme/hq 3"]
MERGE_ASKED_COMMANDS = [
    "gh pr merge -R acme/app 12 --admin", "gh pr merge -R acme/app --admin 12",
    "gh pr merge -R acme/app 12 -R partner/site", "gh pr merge -R acme/app 12 --repo partner/site",
    "gh pr merge -R acme/app 12 -R other/x", "gh pr merge -R acme/app 12 -Rother/x",
    "gh pr merge -R acme/app 12 -R=other/x", "gh pr merge 12 -R other/x",
    "gh pr merge -R acme/app https://github.com/partner/site/pull/3", "gh pr merge -R partner/site 12",
]


def expected(groups, names):
    return [r for g in groups if g["name"] in names for r in g["rules"]]


def repo_rules(groups, names, slugs):
    return [r.replace("<slug>", s) for g in groups if g["name"] in names for s in slugs for r in g["rules"]]


def baseline(groups):
    return [r for g in groups if g["when_free"] == "deny" for r in g["rules"]]


def diff_lists(errors, label, got, want):
    if sorted(got) != sorted(want):
        errors.append(f"{label} differs: extra {sorted(set(got) - set(want))}, missing {sorted(set(want) - set(got))}")
    if len(got) != len(set(got)):
        errors.append(f"{label} has a rule twice")


def examples(groups):
    """The exact lists of each example org, written independently of generate()."""
    reads = {"read-github", "github-api-read", "sync-hq", "plugin-files", "edit-hq"}
    guards = expected(groups, {"github-api-write", "confirm-reset"})
    still_ok = {"release", "settings", "secrets", "delete"}
    # Every example but own-repos has the protected repo partner/site, so push-current asks there.
    base = [SKILL_RULE] + expected(groups, reads | {"commit-hq"})
    push = expected(groups, {"push-current"})
    asks = repo_rules(groups, {"issues", "comments", "pull-requests"}, ["partner/site"]) + push
    default = (base, asks + expected(groups, still_ok) + ["Bash(gh pr merge *)"] + guards)
    own_repos = (base + push, expected(groups, still_ok) + ["Bash(gh pr merge *)"] + guards)
    merge_notice = (base + repo_rules(groups, {"merge"}, ["acme/app", "acme/hq"]),
                    asks + ["Bash(gh pr merge -R partner/site *)"] + expected(groups, still_ok)
                    + expected(groups, {"merge-guards"}) + guards)
    strict = ([SKILL_RULE] + expected(groups, reads),
              [general(r) for r in expected(groups, {"issues", "comments", "tracker", "commit-hq"})]
              + ["Bash(gh pr create -R partner/site *)", "Bash(gh pr merge *)"]
              + expected(groups, still_ok | {"push-current"}) + guards)
    all_free = (base + repo_rules(groups, {"merge"}, ["acme/app", "acme/hq"]),
                repo_rules(groups, {"issues", "comments", "pull-requests", "merge"}, ["partner/site"]) + push
                + expected(groups, {"merge-guards"}) + guards)
    return {"default": default, "own-repos": own_repos, "merge-notice": merge_notice, "strict": strict, "all-free": all_free}


def check(groups, retired):
    errors = []
    actions = known_actions()
    table = {r for g in groups for r in g["rules"]}
    base = baseline(groups)

    # The detector itself: these must be caught, and these must pass.
    for rule in ("Bash(sh *check-boot-set.sh*)", "Bash(bash -c *)", "Bash(python3 -c *)", "Bash(env *)",
                 "Bash(FOO=1 node *)", "Bash(sh:*)", "Bash(* --version)", "Bash(/usr/bin/zsh *)", "Bash(cp *)",
                 "Bash(git rev-list *)", "Bash(git -C * status *)", "Bash(git pull:*)", "Bash(git log *)",
                 "Bash(git diff:*)", "Bash(git push *)", "Bash(git *)", "Bash(git remote:*)",
                 "Bash(gh issue create -R acme/app *)", "Bash(gh issue comment:*)", "Bash(gh api *)",
                 "Bash(gh auth status *)", "Bash(gh project item-add 3 --owner acme *)", "Bash(gh pr merge *)",
                 "Bash(gh pr merge -R acme/app *)", "Bash(git push origin *)", "Bash(gh api repos/x *)"):
        if not risk(rule):
            errors.append(f"detector: does not flag {rule}")
    for rule in ("Bash(gh pr merge *)", "Bash(gh pr merge -R acme/* *)", "Bash(gh pr merge -R * *)",
                 "Bash(gh pr merge -R acme/app 12 *)", "Bash(gh api repos/x *)", "Bash(git push *)"):
        if not risk(rule, guarded_ok=True):
            errors.append(f"detector: does not flag {rule} even with guarded wildcards allowed")
    for rule in ("Bash(gh issue list *)", "Bash(git pull)", "Bash(sh /opt/tool/check.sh)", "Edit(/**)",
                 "Bash(shellcheck *)", "Bash(git rev-list --count HEAD)", "Bash(git commit *)", "Bash(git add:*)",
                 "Bash(git remote add *)", "Bash(git -C /x status)", "Bash(gh auth status)",
                 "Bash(gh search issues *)", "Bash(gh project item-list:*)", "Bash(mkdir *)",
                 "Bash(git push)", "Bash(git push -u origin HEAD)"):
        if risk(rule):
            errors.append(f"detector: flags {rule}")
    for rule in ("Bash(gh api *)", "Bash(gh pr merge -R acme/app *)", "Bash(gh pr merge -R acme/my_app.io-2 *)"):
        if risk(rule, guarded_ok=True):
            errors.append(f"detector: flags guarded wildcard {rule}")

    if not retired:
        errors.append("gates/permissions.md: no rule under \"Retired rules\"")
    for rule in retired:
        if rule in table:
            errors.append(f"retired rule still in the table: {rule}")
    for needed in ("Bash(git push *)", "Bash(gh repo delete *)", "Bash(gh release delete *)"):
        if needed not in retired:
            errors.append(f"0.16.0 retired rule missing: {needed}")
    names = [g["name"] for g in groups]
    if len(names) != len(set(names)):
        errors.append("a group name appears twice")
    for g in groups:
        mode = g["when_free"]
        if mode not in ("allow", "ask", "guard", "deny") and not (mode.startswith("guard if ") and mode[9:] in names):
            errors.append(f"group {g['name']}: \"When free\" is {mode!r}, not allow, ask, guard, guard if <group> or deny")
        if mode == "allow":
            for rule in g["rules"]:
                why = risk(rule, guarded_ok=True)
                if why:
                    errors.append(f"group {g['name']} is marked allow but has a rule that is never allowed ({why}): {rule}")
                need = guards_of(rule)
                if need:
                    have = {r for x in groups if x["when_free"] == "guard" or x["when_free"] == f"guard if {g['name']}" for r in x["rules"]}
                    if not set(need) <= have:
                        errors.append(f"group {g['name']}: guarded wildcard {rule} lacks guards in the table: {sorted(set(need) - have)}")
        if mode == "deny" and any(not r.startswith("Bash(") for r in g["rules"]):
            errors.append(f"deny group {g['name']} has a non-Bash rule")
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

    # push-current: exact forms only
    push = [g for g in groups if g["name"] == "push-current"]
    if len(push) != 1 or push[0]["rules"] != PUSH_CURRENT or any("*" in r for r in push[0]["rules"]):
        errors.append(f"push-current rules are not exactly {PUSH_CURRENT}")
    elif push[0]["when_free"] != "allow" or push[0]["actions"] != ["hq-commit", "push-non-deploy-branch"]:
        errors.append("push-current: expected actions hq-commit, push-non-deploy-branch, marked allow")
    if "Bash(git push *)" in table:
        errors.append("the table still has Bash(git push *)")
    # merge: repo scope, marked allow; guards always with it
    if guards_of("Bash(gh pr merge -R <slug> *)") and [g["rules"] for g in groups if g["name"] == "merge-guards"] != [MERGE_GUARDS]:
        errors.append(f"merge-guards rules are not exactly {MERGE_GUARDS}")
    if [g["rules"] for g in groups if g["name"] == "github-api-write"] != [API_GUARDS]:
        errors.append(f"github-api-write rules are not exactly {API_GUARDS}")
    # deny baseline: the rules of the design must be there
    if len(base) != 32:
        errors.append(f"deny baseline: expected 32 rules, got {len(base)}")
    if any("-*f*" in r and "clean" not in r for r in base):
        errors.append("deny baseline: a -*f* rule would match `git push -u origin feature`")
    if "removed from `ask` only" not in DOC.read_text(encoding="utf-8"):
        errors.append("gates/permissions.md: the retired git push rule must say it is removed from `ask` only")
    for must in ("Bash(git * push *--force*)", "Bash(git * push -f*)", "Bash(git * push * -f*)",
                 "Bash(git * push *--delete*)", "Bash(git push * ':*)", 'Bash(git push * ":*)',
                 "Bash(git push *--force*)", "Bash(git push -f*)", "Bash(git push * -f*)", "Bash(git push * +*)",
                 "Bash(git push *--delete*)", "Bash(git push -d*)", "Bash(git push * -d*)", "Bash(git push * :*)",
                 "Bash(git push *--mirror*)", "Bash(git push *--prune*)", "Bash(git filter-branch*)",
                 "Bash(git filter-repo*)", "Bash(git reflog expire*)", "Bash(git reflog delete*)",
                 "Bash(git clean *-*f*)", "Bash(git clean *--force*)", "Bash(gh repo delete*)",
                 "Bash(gh release delete*)"):
        if must not in base:
            errors.append(f"deny baseline lacks {must}")
    if len([r for r in base if r.startswith("Bash(gh api ")]) != 8:
        errors.append("deny baseline: expected 8 gh api DELETE rules")
    reset = [g for g in groups if g["name"] == "confirm-reset"]
    if len(reset) != 1 or reset[0]["rules"] != RESET_ASK or reset[0]["when_free"] != "guard":
        errors.append(f"confirm-reset is not exactly {RESET_ASK}, marked guard")
    for rule in ("Bash(gh repo delete *)", "Bash(gh release delete *)"):
        if rule in table:
            errors.append(f"{rule} should have left the delete group")

    ok_groups = {g["name"] for g in groups if g["actions"] and tier_of(g["actions"], DEFAULT_ORG["gates"]) == "ok"}
    if not {"merge", "release", "settings", "secrets", "delete", "github-api-write"} <= ok_groups:
        errors.append("default table: an ask group is not ok-tier: " + ", ".join(sorted(ok_groups)))

    deny_res = [(r, rule_regex(r)) for r in base]
    for label, org in ORGS:
        allow, ask, deny = generate(org, groups)
        both = set(allow) & set(ask)
        if both:
            errors.append(f"{label}: rules in both allow and ask: {sorted(both)}")
        for rule in allow:
            why = risk(rule, guarded_ok=True)
            if why:
                errors.append(f"{label}: allow has a rule that is never allowed ({why}): {rule}")
            need = guards_of(rule)
            if need and not set(need) <= set(ask):
                errors.append(f"{label}: guarded wildcard {rule} in allow without its guards in ask: {sorted(set(need) - set(ask))}")
            for r, rx in deny_res:
                if rx.match(rule[5:-1] if rule.startswith("Bash(") else rule):
                    errors.append(f"{label}: allow rule {rule} matches deny rule {r}")
        missing = [r for r in base if r not in deny]
        if missing:
            errors.append(f"{label}: deny baseline incomplete: {missing}")
        for r in RESET_ASK:
            if r not in ask:
                errors.append(f"{label}: {r} not in ask")
        for g in groups:
            if g["actions"] and tier_of(g["actions"], org["gates"]) == "ok" and g["when_free"] != "guard":
                leaked = [r for r in allow if r in g["rules"] or r.startswith(general(g["rules"][0])[:-2])]
                if leaked:
                    errors.append(f"{label}: ok-tier group {g['name']} in allow: {leaked}")
        # tier mapping: the push-current group
        tier = tier_of(["hq-commit", "push-non-deploy-branch"], org["gates"])
        want = "allow" if tier in ("free", "notice") and not has_protected(org) else "ask"
        for r in PUSH_CURRENT:
            if (r in allow) != (want == "allow") or (r in ask) != (want == "ask"):
                errors.append(f"{label}: push-current rule {r} is not in {want} (tier {tier})")
        # real spellings
        for c in DENY_COMMANDS:
            if verdict(c, allow, ask, deny) != "deny":
                errors.append(f"{label}: {c!r} is not refused")
        for c in RESET_COMMANDS:
            if verdict(c, allow, ask, deny) != "ask":
                errors.append(f"{label}: {c!r} does not ask")
        for c in API_WRITE_COMMANDS:
            if verdict(c, allow, ask, deny) != "ask":
                errors.append(f"{label}: {c!r} does not ask")
        for c in PUSH_OK_COMMANDS:
            got = verdict(c, allow, ask, deny)
            if got != want:
                errors.append(f"{label}: {c!r} is {got}, expected {want}")
        for c in PUSH_DEFAULT_COMMANDS:
            got = verdict(c, allow, ask, deny)
            if got != "default":
                errors.append(f"{label}: {c!r} is {got}, expected default (no rule)")
        research = tier_of(["research"], org["gates"])
        for c in API_READ_COMMANDS:
            got = verdict(c, allow, ask, deny)
            if got != ("allow" if research in ("free", "notice") else "default"):
                errors.append(f"{label}: {c!r} is {got}")
        merge_tier = tier_of(["merge"], org["gates"])
        for c in MERGE_ALLOWED_COMMANDS:
            got = verdict(c, allow, ask, deny)
            if got != ("allow" if merge_tier in ("free", "notice") else "ask"):
                errors.append(f"{label}: {c!r} is {got}")
        for c in MERGE_ASKED_COMMANDS:
            if verdict(c, allow, ask, deny) != "ask":
                errors.append(f"{label}: {c!r} does not ask")
        for rule in allow:
            if rule.startswith("Bash(gh pr merge") and merge_tier == "ok":
                errors.append(f"{label}: merge is ok but {rule} is in allow")
        if merge_tier == "ok" and "Bash(gh pr merge *)" not in ask:
            errors.append(f"{label}: merge is ok but Bash(gh pr merge *) is not in ask")
        if any(r.startswith("Bash(gh pr merge -R") and r.endswith("/*)") for r in allow):
            errors.append(f"{label}: an owner pattern is allowed for merge")

    # Examples
    want_lists = examples(groups)
    for label, org in ORGS:
        allow, ask, deny = generate(org, groups)
        want_allow, want_ask = want_lists[label]
        diff_lists(errors, f"{label} example allow", allow, want_allow)
        diff_lists(errors, f"{label} example ask", ask, want_ask)
        diff_lists(errors, f"{label} example deny", deny, base)
    allow, ask, _ = generate(DEFAULT_ORG, groups)
    if any(r in allow for r in expected(groups, {"merge"})):
        errors.append("default example: merge (ok) has an allow rule")
    if "Bash(gh pr merge -R acme/app *)" not in generate(MERGE_NOTICE_ORG, groups)[0]:
        errors.append("merge-notice example: no merge allow rule for acme/app")

    # Merge: keeps other keys and own rules, idempotent, tightens on regeneration
    old_ask = ["Bash(git push *)", "Bash(gh api *)", "Bash(gh repo delete *)", "Bash(gh release delete *)",
               "Bash(gh pr merge *)"]
    before = {
        "enabledPlugins": {"ceo-of-agents@ceo-of-agents": True},
        "attribution": {"commit": "", "pr": ""},
        "permissions": {"allow": ["Bash(make test)", SKILL_RULE, "Bash(gh issue create -R old/repo *)",
                                  "Bash(gh issue create -R acme/app *)", "Bash(gh project item-add 3 --owner acme *)"]
                                 + retired,
                        "ask": list(retired) + old_ask + ["Bash(my own ask)"],
                        "deny": ["mcp__other", "Bash(git push *--force*)", "Bash(my own deny)"],
                        "defaultMode": "default"},
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
    if "Bash(my own ask)" not in p["ask"] or "Bash(my own deny)" not in p["deny"]:
        errors.append("merge dropped an own ask or deny rule")
    if "Bash(gh issue create -R old/repo *)" in p["allow"]:
        errors.append("merge kept a managed rule for an unregistered repo")
    if "Bash(gh issue create -R acme/app *)" in p["allow"] or "Bash(gh project item-add 3 --owner acme *)" in p["allow"]:
        errors.append("merge kept a 0.15.0 allow rule for a GitHub write")
    if "Bash(git push *)" not in p["allow"]:
        errors.append("merge removed a user's own Bash(git push *) from allow")
    kept_user = merge({"permissions": {"allow": ["Bash(git push *)"], "deny": ["Bash(git push *)"]}}, org, groups, retired)["permissions"]
    if "Bash(git push *)" not in kept_user["allow"] or "Bash(git push *)" not in kept_user["deny"]:
        errors.append("a user's Bash(git push *) in allow or deny did not survive regeneration")
    left = [r for r in p.get("allow", []) + p.get("ask", []) if r in retired and r not in ASK_ONLY_RETIRED]
    if left:
        errors.append(f"merge kept retired rules: {left}")
    if "Bash(gh api *)" in p["ask"] or "Bash(gh api *)" not in p["allow"]:
        errors.append("merge did not move Bash(gh api *) from ask to allow")
    if "Bash(git push *)" in p["ask"]:
        errors.append("merge kept Bash(git push *) in ask")
    if "Bash(git push *)" in once["permissions"].get("ask", []) or merge({"permissions": {"ask": ["Bash(git push *)"]}}, org, groups, retired)["permissions"].get("ask", []).count("Bash(git push *)"):
        errors.append("merge kept the retired Bash(git push *) in ask")
    if p["allow"].count(SKILL_RULE) != 1:
        errors.append("merge: Skill rule not exactly once")
    if p["deny"][:1] != ["mcp__other"] or "mcp__work" not in p["deny"] or any(r not in p["deny"] for r in base):
        errors.append(f"merge deny wrong: {p['deny']}")
    if p["deny"].count("Bash(git push *--force*)") != 1:
        errors.append("merge: a baseline rule is not exactly once in deny")
    freed = copy.deepcopy(org)
    freed["repos"][2]["protected"] = False
    after = merge(once, freed, groups, retired)
    if "Bash(gh issue comment -R partner/site *)" in after["permissions"].get("ask", []) or \
            "Bash(gh issue comment -R partner/site *)" in after["permissions"].get("allow", []):
        errors.append("regeneration after freeing a repo kept its ask rules or allowed them")
    # Option: any protected repo makes push-current ask; freeing the last one moves it back to allow.
    if any(r not in once["permissions"]["ask"] or r in once["permissions"]["allow"] for r in PUSH_CURRENT):
        errors.append("an org with a protected repo does not ask for push-current")
    if any(r not in after["permissions"]["allow"] or r in after["permissions"]["ask"] for r in PUSH_CURRENT):
        errors.append("regeneration after freeing the last protected repo did not move push-current to allow")
    strict_after = merge(once, dict(org, gates=STRICT_ORG["gates"]), groups, retired)
    if any(r.startswith("Bash(gh issue create -R") for r in strict_after["permissions"]["allow"]):
        errors.append("regeneration to a stricter org kept gh issue create in allow")
    if any(r in strict_after["permissions"]["allow"] for r in PUSH_CURRENT):
        errors.append("regeneration with push in ok kept push-current in allow")
    notice_after = merge(once, dict(org, gates=MERGE_NOTICE_ORG["gates"]), groups, retired)
    if "Bash(gh pr merge *)" in notice_after["permissions"]["ask"] or \
            "Bash(gh pr merge -R acme/app *)" not in notice_after["permissions"]["allow"]:
        errors.append("regeneration to merge notice did not replace the general ask by per-repo allow")
    back = merge(notice_after, org, groups, retired)
    if "Bash(gh pr merge -R acme/app *)" in back["permissions"]["allow"] or "Bash(gh pr merge *--admin*)" in back["permissions"]["ask"]:
        errors.append("regeneration back to merge ok kept merge allow rules or the merge guards")
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
