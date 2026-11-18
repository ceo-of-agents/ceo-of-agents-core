#!/usr/bin/env python3
"""Check the setup answers format and its samples.

Validates the example in schemas/setup-answers.yaml and every
examples/setup-answers/*.yaml against the rules documented in the schema file
(which follow the questions of skills/init-fleet/SKILL.md): required keys,
allowed values, ids, level and purpose constraints, department rules for the
four ways to build them, gates, models, policy, repos and attribution, `later`
only where a question accepts it, and unknown keys. Without --file it also
checks that there is a sample for each purpose and for a holding, that the
README lists every sample, and that the samples together cover the documented
cases. With --file <path> it checks that one file only.
Needs PyYAML.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT / "schemas" / "setup-answers.yaml"
SAMPLES = ROOT / "examples" / "setup-answers"
GATES_FILE = ROOT / "gates" / "default.md"
CATALOG = ROOT / "catalog"

PURPOSES = ("job", "product", "startup", "company", "personal")
PERSONAL_ONLY = ("health", "money", "paperwork")
ADVISORY = ("legal", "finance", "tax") + PERSONAL_ONLY
TIERS = ("opus", "sonnet", "haiku")
GATE_TIERS = ("free", "notice", "ok")
NEVER_MOVE = ("file-or-sign", "make-payment")
ABILITIES_ADD = ("Bash", "Agent(worker)", "WebSearch", "WebFetch")
ABILITIES_DROP = ("Bash", "Agent", "WebSearch", "WebFetch")
STAGES = {
    "company-level": ("idea", "building", "live"),
    "job": ("new in the role", "settled", "in transition"),
    "holding": ("starting", "growing", "steady"),
    "personal": ("setting up", "running"),
}
ID_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
AGENT_RE = re.compile(r"^[a-z][a-z0-9-]*$")
LANG_RE = re.compile(r"^[a-z]{2}$")
SLUG_RE = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
PIN_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
PROJECT_RE = re.compile(r"^https://github\.com/(orgs|users)/[A-Za-z0-9-]+/projects/[0-9]+$")
LATER_PATHS = {"names.ceo", "policy", "employer_rules", "remote.hq", "policies_repo.remote", "repos", "roadmap", "attribution"}
TOP_KEYS = ("schema", "language", "org", "services", "ceo", "about", "departments", "names", "gates", "models",
            "policy", "employer_rules", "remote", "policies_repo", "repos", "issues_home", "roadmap",
            "attribution", "enable_plugin")
ALWAYS_REQUIRED = ("schema", "language", "org", "ceo", "about", "departments", "names", "gates", "models",
                   "remote", "attribution", "enable_plugin")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def gate_tiers():
    """Action id -> default tier, from the table at the top of gates/default.md."""
    tiers = {}
    for line in GATES_FILE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\|\s*(free|notice|ok)\s*\|.*\|\s*((?:`[a-z-]+`(?:,\s*)?)+)\s*\|\s*$", line)
        if match:
            for action in re.findall(r"`([a-z-]+)`", match.group(2)):
                tiers[action] = match.group(1)
    return tiers


def catalog_entries():
    """Catalog id -> {role, tools}, from catalog/<id>/agent.md."""
    entries = {}
    for folder in sorted(CATALOG.iterdir()):
        agent = folder / "agent.md"
        if not agent.is_file():
            continue
        text = agent.read_text(encoding="utf-8")
        tools = re.search(r"^tools:\s*(.+)$", text, re.MULTILINE)
        role = re.search(r"the (.+?) department of", text)
        entries[folder.name] = {
            "role": role.group(1) if role else folder.name,
            "tools": tools.group(1).strip() if tools else "",
        }
    return entries


def slug(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def is_line(value):
    return is_text(value) and "\n" not in value.strip()


class Checker:
    def __init__(self, doc, label):
        self.doc = doc
        self.label = label
        self.errors = []
        self.gates = gate_tiers()
        self.catalog = catalog_entries()

    def err(self, path, message):
        self.errors.append(f"{self.label}: {path}: {message}" if path else f"{self.label}: {message}")

    def mapping(self, value, path, required=(), optional=()):
        """Return the mapping, or None after reporting a wrong type. Reports missing and unknown keys."""
        if not isinstance(value, dict):
            self.err(path, "must be a mapping")
            return None
        for key in required:
            if key not in value:
                self.err(path, f"missing key `{key}`")
        for key in value:
            if key not in required and key not in optional:
                self.err(path, f"unknown key `{key}`")
        return value

    def text_list(self, value, path, allow_empty=False):
        if not isinstance(value, list) or (not value and not allow_empty):
            self.err(path, "must be a non-empty list of text" if not allow_empty else "must be a list of text")
            return []
        for i, item in enumerate(value):
            if not is_text(item):
                self.err(f"{path}[{i}]", "must be non-empty text")
        return value

    def item_owner_list(self, value, path, allow_empty=False):
        if not isinstance(value, list) or (not value and not allow_empty):
            self.err(path, "must be a non-empty list of {item, owner}")
            return
        for i, entry in enumerate(value):
            m = self.mapping(entry, f"{path}[{i}]", required=("item", "owner"))
            if m:
                for key in ("item", "owner"):
                    if key in m and not is_text(m[key]):
                        self.err(f"{path}[{i}].{key}", "must be non-empty text")

    def tier(self, value, path):
        if value not in TIERS:
            self.err(path, f"must be one of {', '.join(TIERS)}")
            return False
        return True

    def deferrable(self, value, path, check):
        """`none`, `later`, or a value that `check` validates."""
        if value in ("none", "later"):
            return
        check(value, path)

    def run(self):
        doc = self.mapping(self.doc, "", required=ALWAYS_REQUIRED, optional=[k for k in TOP_KEYS if k not in ALWAYS_REQUIRED])
        if doc is None:
            return self.errors
        self.walk_later(doc, "")
        if doc.get("schema") != "setup-answers/1":
            self.err("schema", 'must be exactly "setup-answers/1"')
        self.check_language(doc.get("language"))
        purpose, level = self.check_org(doc.get("org"))
        self.check_services(doc)
        self.check_ceo(doc.get("ceo"))
        self.check_about(doc.get("about"), purpose, level)
        depts = self.check_departments(doc.get("departments"), purpose)
        self.check_names(doc.get("names"), depts)
        self.check_gates(doc.get("gates"))
        self.check_models(doc.get("models"), depts)
        self.check_case_keys(doc, purpose, level)
        if not isinstance(doc.get("enable_plugin"), bool):
            self.err("enable_plugin", "must be true or false")
        self.check_attribution(doc.get("attribution"))
        return self.errors

    # `later` only where a question accepts it
    def walk_later(self, value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                self.walk_later(item, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                self.walk_later(item, f"{path}[{i}]")
        elif value == "later" and path not in LATER_PATHS:
            self.err(path, "`later` is not allowed here (the wizard never accepts a deferral for this answer)")

    def check_language(self, value):
        m = self.mapping(value, "language", required=("chat", "files"))
        if m:
            for key in ("chat", "files"):
                if key in m and not (isinstance(m[key], str) and LANG_RE.match(m[key])):
                    hint = " (quote it: `\"no\"`; YAML reads an unquoted no as false)" if m[key] is False else ""
                    self.err(f"language.{key}", f"must be a two-letter code such as en{hint}")

    def check_org(self, value):
        m = self.mapping(value, "org", required=("purpose", "id", "name"), optional=("level",))
        if not m:
            return None, None
        purpose = m.get("purpose")
        if purpose not in PURPOSES:
            self.err("org.purpose", f"must be one of {', '.join(PURPOSES)}")
        level = m.get("level")
        if purpose == "company":
            if level not in ("company", "holding"):
                self.err("org.level", "is required for purpose company: company or holding")
        elif level not in (None, "company"):
            self.err("org.level", f"must be company (or absent) for purpose {purpose}: only purpose company can be a holding")
        if purpose != "company":
            level = "company"
        if not (isinstance(m.get("id"), str) and ID_RE.match(m["id"])):
            hint = " (quote an id that YAML reads as a boolean, such as \"NO\" or \"ON\")" if isinstance(m.get("id"), bool) else ""
            self.err("org.id", f"must match ^[A-Z][A-Z0-9]{{1,7}}$ (2 to 8 characters, capital letters and digits, starting with a letter){hint}")
        if not is_text(m.get("name")):
            self.err("org.name", "must be non-empty text")
        return purpose, level

    def check_services(self, doc):
        if "services" in doc and doc["services"] not in (False, "no"):
            self.err("services", "can only be `no`: reading services needs the CEO's confirmation per service in the chat")

    def check_ceo(self, value):
        m = self.mapping(value, "ceo", required=("profile",))
        if m and m.get("profile") not in ("technical", "non-technical"):
            self.err("ceo.profile", "must be technical or non-technical")

    def check_about(self, value, purpose, level):
        m = self.mapping(value, "about", required=("what", "why", "stage"))
        if not m:
            return
        for key in ("what", "why"):
            if key in m and not is_text(m[key]):
                self.err(f"about.{key}", "must be non-empty text")
        if purpose in PURPOSES:
            if purpose == "job":
                stages = STAGES["job"]
            elif purpose == "personal":
                stages = STAGES["personal"]
            elif level == "holding":
                stages = STAGES["holding"]
            else:
                stages = STAGES["company-level"]
            if m.get("stage") not in stages:
                self.err("about.stage", f"must be one of {', '.join(stages)} for this purpose and level")

    # departments
    def check_departments(self, value, purpose):
        """Return {id: {"from": ..., "display_role": role name or None, "agent": own name or None}}."""
        depts = {}
        if not isinstance(value, list):
            self.err("departments", "must be a list ([] for no department)")
            return depts
        replaced = []
        for i, item in enumerate(value):
            path = f"departments[{i}]"
            if not isinstance(item, dict):
                self.err(path, "must be a mapping")
                continue
            way = item.get("from")
            if way not in ("catalog", "custom", "own"):
                self.err(f"{path}.from", "must be catalog, custom or own")
                continue
            dept_id = item.get("id")
            if not isinstance(dept_id, str):
                self.err(f"{path}.id", "must be text")
                continue
            if dept_id in depts:
                self.err(f"{path}.id", f"duplicate department id `{dept_id}`")
                continue
            if way == "catalog":
                depts[dept_id] = {"from": way, "role": self.check_catalog(item, path, dept_id, purpose)}
            elif way == "custom":
                depts[dept_id] = {"from": way, "role": self.check_custom(item, path, dept_id)}
            else:
                depts[dept_id] = {"from": way, "role": None, "agent": self.check_own(item, path, dept_id, purpose, replaced)}
        for target in replaced:
            for dept_id, info in depts.items():
                if info["from"] == "catalog" and dept_id == target:
                    self.err("departments", f"`{target}` is replaced by an own agent and must not also appear as from catalog")
        return depts

    def check_catalog(self, item, path, dept_id, purpose):
        m = self.mapping(item, path, required=("from", "id"), optional=("changes",))
        entry = self.catalog.get(dept_id)
        if entry is None:
            self.err(f"{path}.id", f"`{dept_id}` is not a catalog id ({', '.join(sorted(self.catalog))})")
            return None
        if dept_id in PERSONAL_ONLY and purpose != "personal":
            self.err(f"{path}.id", f"`{dept_id}` is offered only with purpose personal")
        if m and "changes" in m:
            self.check_changes(m["changes"], f"{path}.changes", dept_id, entry)
        return entry["role"]

    def check_changes(self, value, path, dept_id, entry):
        m = self.mapping(value, path, optional=("scope_add", "scope_drop", "never", "abilities_add", "abilities_drop"))
        if not m:
            return
        if not any(m.get(k) for k in m):
            self.err(path, "needs at least one of scope_add, scope_drop, never, abilities_add, abilities_drop")
        if "scope_add" in m:
            self.text_list(m["scope_add"], f"{path}.scope_add")
        for key in ("scope_drop", "never"):
            if key in m:
                self.item_owner_list(m[key], f"{path}.{key}")
        tools = entry["tools"]
        has = {
            "Bash": re.search(r"(^|,\s*)Bash(,|$)", tools) is not None,
            "Agent(worker)": re.search(r"Agent\([^)]*\bworker\b", tools) is not None,
            "WebSearch": "WebSearch" in tools,
            "WebFetch": "WebFetch" in tools,
            "Agent": "Agent(" in tools,
        }
        added = []
        for i, add in enumerate(m.get("abilities_add") or []):
            p = f"{path}.abilities_add[{i}]"
            am = self.mapping(add, p, required=("ability", "reason"))
            if not am:
                continue
            ability = am.get("ability")
            if ability not in ABILITIES_ADD:
                self.err(f"{p}.ability", f"must be one of {', '.join(ABILITIES_ADD)}")
                continue
            if not is_line(am.get("reason")):
                self.err(f"{p}.reason", "must be one line of text (the reason for the grant)")
            if dept_id in ADVISORY and ability in ("Bash", "Agent(worker)"):
                self.err(p, f"`{dept_id}` is advisory and never gains {ability}")
            if has[ability] or ability in added:
                self.err(p, f"`{ability}` is already there (in the catalog entry or added twice)")
            added.append(ability)
        if "Agent(worker)" in added and not (has["Bash"] or "Bash" in added):
            self.err(f"{path}.abilities_add", "Agent(worker) is allowed only together with Bash")
        dropped = []
        drops = m.get("abilities_drop")
        if drops is not None:
            if not isinstance(drops, list) or not drops:
                self.err(f"{path}.abilities_drop", "must be a non-empty list")
                drops = []
            for i, ability in enumerate(drops):
                p = f"{path}.abilities_drop[{i}]"
                if ability not in ABILITIES_DROP:
                    self.err(p, f"must be one of {', '.join(ABILITIES_DROP)}")
                elif not has[ability]:
                    self.err(p, f"`{dept_id}` has no {ability} to drop")
                elif ability in dropped:
                    self.err(p, f"`{ability}` is dropped twice")
                elif ability in added:
                    self.err(p, f"`{ability}` is both added and dropped")
                dropped.append(ability)
        if "Bash" in dropped and has["Agent(worker)"] and "Agent" not in dropped:
            self.err(f"{path}.abilities_drop", "dropping Bash from an entry with Agent(worker) needs Agent dropped too")

    def check_custom(self, item, path, dept_id):
        keys = ("from", "id", "role", "purpose", "scope", "triggers", "exclusions", "core_job", "commands")
        m = self.mapping(item, path, required=keys)
        if not KEBAB_RE.match(dept_id):
            self.err(f"{path}.id", "must be kebab-case: letters, digits and hyphens")
        if not m:
            return None
        for key in ("role", "purpose", "core_job"):
            if key in m and not is_line(m[key]):
                self.err(f"{path}.{key}", "must be one line of text")
        for key in ("scope", "triggers"):
            if key in m:
                self.text_list(m[key], f"{path}.{key}")
        if "exclusions" in m:
            self.item_owner_list(m["exclusions"], f"{path}.exclusions")
        if "commands" in m:
            cm = self.mapping(m["commands"], f"{path}.commands", required=("needed",), optional=("reason",))
            if cm:
                if not isinstance(cm.get("needed"), bool):
                    self.err(f"{path}.commands.needed", "must be true or false")
                elif cm["needed"] and not is_line(cm.get("reason")):
                    self.err(f"{path}.commands.reason", "is required when commands are needed: one line, the reason for the grant")
                elif not cm["needed"] and "reason" in cm:
                    self.err(f"{path}.commands.reason", "must be absent when commands are not needed")
        return m.get("role") if is_text(m.get("role")) else None

    def check_own(self, item, path, dept_id, purpose, replaced):
        keys = ("from", "id", "name", "kind", "location", "purpose", "use_when", "must_not", "replaces")
        m = self.mapping(item, path, required=keys)
        if not KEBAB_RE.match(dept_id):
            self.err(f"{path}.id", "must be kebab-case: letters, digits and hyphens")
        if not m:
            return None
        name = m.get("name")
        if not is_text(name) or re.search(r"\s", name):
            self.err(f"{path}.name", "must be non-empty text without spaces (its name as Claude Code knows it)")
            name = None
        if m.get("kind") not in ("agent", "skill"):
            self.err(f"{path}.kind", "must be agent or skill")
        for key in ("location", "purpose"):
            if key in m and not is_line(m[key]):
                self.err(f"{path}.{key}", "must be one line of text")
        if "use_when" in m:
            self.text_list(m["use_when"], f"{path}.use_when")
        if "must_not" in m:
            self.item_owner_list(m["must_not"], f"{path}.must_not")
        replaces = m.get("replaces")
        if replaces != "none" and "replaces" in m:
            if replaces not in self.catalog:
                self.err(f"{path}.replaces", "must be none or a catalog id")
            elif replaces in PERSONAL_ONLY and purpose != "personal":
                self.err(f"{path}.replaces", f"`{replaces}` is offered only with purpose personal")
            else:
                replaced.append(replaces)
        return name

    def check_names(self, value, depts):
        m = self.mapping(value, "names", required=("cos", "ceo", "departments"), optional=("agents",))
        if not m:
            return
        if not is_text(m.get("cos")):
            self.err("names.cos", "must be non-empty text: Chief of staff or a persona name")
        if "ceo" in m and not is_text(m["ceo"]):
            self.err("names.ceo", "must be a name or `later`")
        display = m.get("departments")
        if isinstance(display, dict):
            for dept_id in depts:
                if dept_id not in display:
                    self.err("names.departments", f"missing a display name for `{dept_id}`")
            for key, name in display.items():
                if key not in depts:
                    self.err(f"names.departments.{key}", "is not a department id of this file")
                elif not is_text(name):
                    self.err(f"names.departments.{key}", "must be non-empty text")
        elif display is not None:
            self.err("names.departments", "must be a mapping from every department id to its display name")
            display = {}
        else:
            display = {}
        agents = m.get("agents", {})
        if "agents" in m and not isinstance(agents, dict):
            self.err("names.agents", "must be a mapping from a department id to an agent name")
            agents = {}
        for key, name in agents.items():
            if key not in depts:
                self.err(f"names.agents.{key}", "is not a department id of this file")
            elif depts[key]["from"] == "own":
                self.err(f"names.agents.{key}", "a brought-in agent or skill keeps its own name")
            elif not (isinstance(name, str) and AGENT_RE.match(name)):
                self.err(f"names.agents.{key}", "must match ^[a-z][a-z0-9-]*$")
        # derived agent names
        resolved = {}
        for dept_id, info in depts.items():
            if info["from"] == "own":
                if info.get("agent"):
                    resolved[dept_id] = info["agent"]
                continue
            if dept_id in agents and isinstance(agents[dept_id], str):
                resolved[dept_id] = agents[dept_id]
                continue
            shown = display.get(dept_id) if isinstance(display, dict) else None
            if not is_text(shown):
                continue
            if info.get("role") and shown.strip().lower() == info["role"].lower():
                resolved[dept_id] = dept_id
                continue
            derived = slug(shown)
            if not AGENT_RE.match(derived):
                self.err(f"names.departments.{dept_id}", "gives no usable agent name (use Latin letters, or set names.agents)")
                continue
            resolved[dept_id] = derived
        seen = {}
        for dept_id, agent in resolved.items():
            if agent in ("reader", "worker"):
                self.err(f"names.departments.{dept_id}", f"agent name `{agent}` clashes with a generic worker (set names.agents)")
            if agent in seen:
                self.err(f"names.departments.{dept_id}", f"agent name `{agent}` is also the agent of `{seen[agent]}` (set names.agents for one)")
            seen[agent] = dept_id
            for other in depts:
                if other != dept_id and other == agent:
                    self.err(f"names.departments.{dept_id}", f"agent name `{agent}` is the id of department `{other}` (set names.agents)")

    def check_gates(self, value):
        if value == "accept":
            return
        m = self.mapping(value, "gates", optional=("stricter", "looser"))
        if m is None:
            return
        if not m:
            self.err("gates", "must be `accept` or a mapping with stricter and/or looser")
        moved = set()
        for key, targets, toward in (("stricter", ("notice", "ok"), 1), ("looser", ("free", "notice"), -1)):
            if key not in m:
                continue
            moves = m[key]
            if not isinstance(moves, dict) or not moves:
                self.err(f"gates.{key}", "must be a non-empty mapping from an action id to a tier")
                continue
            for action, tier in moves.items():
                p = f"gates.{key}.{action}"
                if action not in self.gates:
                    self.err(p, "is not an action id of gates/default.md")
                    continue
                if action in NEVER_MOVE:
                    self.err(p, f"{action} always needs the CEO's OK and can never move")
                    continue
                if action in moved:
                    self.err(p, "an action is listed once")
                moved.add(action)
                if tier not in targets:
                    self.err(p, f"must be one of {', '.join(targets)}")
                    continue
                here = GATE_TIERS.index(self.gates[action])
                there = GATE_TIERS.index(tier)
                if there == here:
                    self.err(p, f"is already in {tier}")
                elif (there - here) * toward < 0:
                    self.err(p, f"moves {self.gates[action]} to {tier}, which is not {key}")

    def check_models(self, value, depts):
        m = self.mapping(value, "models", required=("cos", "departments"), optional=("overrides", "top_workers"))
        if not m:
            return
        self.tier(m.get("cos"), "models.cos")
        self.tier(m.get("departments"), "models.departments")
        overrides = m.get("overrides", {})
        if "overrides" in m and not isinstance(overrides, dict):
            self.err("models.overrides", "must be a mapping from a department id to a tier")
            overrides = {}
        for dept_id, tier in overrides.items():
            if dept_id not in depts:
                self.err(f"models.overrides.{dept_id}", "is not a department id of this file")
            elif depts[dept_id]["from"] == "own":
                self.err(f"models.overrides.{dept_id}", "a brought-in department has no model: its own file decides")
            self.tier(tier, f"models.overrides.{dept_id}")
        top = m.get("top_workers", [])
        if "top_workers" in m and not isinstance(top, list):
            self.err("models.top_workers", "must be a list of department ids")
            top = []
        for dept_id in top:
            p = "models.top_workers"
            if dept_id not in depts:
                self.err(p, f"`{dept_id}` is not a department id of this file")
            elif depts[dept_id]["from"] == "own":
                self.err(p, f"`{dept_id}` is a brought-in department and has no model")
            elif overrides.get(dept_id, TIERS[0]) != TIERS[0]:
                self.err(p, f"`{dept_id}` runs on {TIERS[0]} with its workers, so it has no other model in overrides")

    # keys that depend on purpose and level
    def check_case_keys(self, doc, purpose, level):
        if purpose not in PURPOSES:
            return
        portfolio = level == "company" and purpose in ("product", "startup", "company")
        cases = (
            ("policy", portfolio, "level company with purpose product, startup or company"),
            ("employer_rules", purpose == "job", "purpose job"),
            ("policies_repo", level == "holding", "level holding"),
            ("repos", level == "company" and purpose != "personal", "level company and purpose not personal"),
            ("roadmap", level == "company" and purpose != "personal", "level company and purpose not personal"),
        )
        for key, applies, where in cases:
            if applies and key not in doc:
                self.err(key, f"is required for {where}")
            elif not applies and key in doc:
                self.err(key, f"does not apply here: only for {where}")
        if portfolio and "policy" in doc:
            self.deferrable(doc["policy"], "policy", self.check_policy)
        if purpose == "job" and "employer_rules" in doc:
            self.deferrable(doc["employer_rules"], "employer_rules", lambda v, p: None if is_text(v) and "\n" not in v.strip() else self.err(p, "must be none, later, or a pointer (a URL or a path)"))
        self.check_remote(doc.get("remote"), purpose)
        if level == "holding" and "policies_repo" in doc:
            self.check_policies_repo(doc["policies_repo"])
        repos = doc.get("repos")
        slugs = []
        if level == "company" and purpose != "personal":
            if "repos" in doc:
                self.deferrable(repos, "repos", self.check_repos)
                if isinstance(repos, list):
                    slugs = [r.get("slug") for r in repos if isinstance(r, dict)]
            if isinstance(repos, list):
                self.check_issues_home(doc, slugs)
            if "roadmap" in doc:
                self.deferrable(doc["roadmap"], "roadmap", self.check_roadmap)
        if "issues_home" in doc and not isinstance(repos, list):
            self.err("issues_home", "does not apply: it is for a list of repos")

    def check_policy(self, value, path):
        m = self.mapping(value, path, required=("repo", "local", "pin"))
        if not m:
            return
        if not isinstance(m.get("repo"), str):
            self.err(f"{path}.repo", 'must be the policies repo git remote, or "" when it has none yet')
        if not is_line(m.get("local")):
            self.err(f"{path}.local", "must be the local clone path of the policies repo")
        if not PIN_RE.match(str(m.get("pin"))):
            self.err(f"{path}.pin", "must be a commit sha, 7 to 40 hex characters (quote it if it is all digits)")

    def check_remote(self, value, purpose):
        m = self.mapping(value, "remote", required=("hq",), optional=("hosted_on",))
        if not m:
            return
        if "hq" in m:
            self.deferrable(m["hq"], "remote.hq", lambda v, p: None if is_line(v) and not re.search(r"\s", v) else self.err(p, "must be none, later, or a git remote URL"))
        if purpose == "job":
            if m.get("hosted_on") not in ("personal", "employer", "undecided"):
                self.err("remote.hosted_on", "is required for purpose job: personal, employer or undecided")
        elif "hosted_on" in m:
            self.err("remote.hosted_on", "does not apply: only for purpose job")

    def check_policies_repo(self, value):
        m = self.mapping(value, "policies_repo", required=("path", "remote"), optional=("ceiling",))
        if not m:
            return
        path = m.get("path")
        if not (is_line(path) and path.startswith("/")) or ".." in str(path).split("/"):
            self.err("policies_repo.path", "must be an absolute path (starting with /) outside the hq folder")
        if "remote" in m:
            self.deferrable(m["remote"], "policies_repo.remote", lambda v, p: None if is_line(v) and not re.search(r"\s", v) else self.err(p, "must be none, later, or a git remote URL"))
        if "ceiling" in m:
            cm = self.mapping(m["ceiling"], "policies_repo.ceiling", required=("cos", "departments", "workers"))
            if cm:
                for key in ("cos", "departments", "workers"):
                    self.tier(cm.get(key), f"policies_repo.ceiling.{key}")

    def check_repos(self, value, path):
        if not isinstance(value, list) or not value:
            self.err(path, "must be none, later, or a non-empty list of repos")
            return
        seen = set()
        for i, repo in enumerate(value):
            p = f"{path}[{i}]"
            m = self.mapping(repo, p, required=("slug", "role", "visibility", "protected", "exists"))
            if not m:
                continue
            repo_slug = m.get("slug")
            if not (isinstance(repo_slug, str) and SLUG_RE.match(repo_slug)):
                self.err(f"{p}.slug", "must be owner/name (owner: letters, digits, -; name: letters, digits, -, _, .)")
            elif repo_slug in seen:
                self.err(f"{p}.slug", f"duplicate repo `{repo_slug}`")
            seen.add(repo_slug)
            if not is_line(m.get("role")):
                self.err(f"{p}.role", "must be a short word or two: code, site, docs, ...")
            if m.get("visibility") not in ("public", "private"):
                self.err(f"{p}.visibility", "must be public or private")
            for key in ("protected", "exists"):
                if not isinstance(m.get(key), bool):
                    self.err(f"{p}.{key}", "must be true or false")

    def check_issues_home(self, doc, slugs):
        if "issues_home" not in doc:
            self.err("issues_home", "is required when repos is a list (exactly one issues home): a listed slug, or hq")
            return
        home = doc["issues_home"]
        if home == "hq":
            hq = (doc.get("remote") or {}).get("hq") if isinstance(doc.get("remote"), dict) else None
            if not (isinstance(hq, str) and "github.com" in hq):
                self.err("issues_home", "hq needs a hq remote URL on GitHub in remote.hq")
        elif home not in slugs:
            self.err("issues_home", "must be one of the listed repo slugs, or hq")

    def check_roadmap(self, value, path):
        m = self.mapping(value, path, required=("url", "status_field"))
        if not m:
            return
        if not (isinstance(m.get("url"), str) and PROJECT_RE.match(m["url"])):
            self.err(f"{path}.url", "must be https://github.com/orgs/<owner>/projects/<number> or https://github.com/users/<owner>/projects/<number>")
        if not is_line(m.get("status_field")):
            self.err(f"{path}.status_field", "must be the name of the status field")

    def check_attribution(self, value):
        if value in ("default", "none", "later"):
            return
        m = self.mapping(value, "attribution", required=("commit", "pr"))
        if m:
            for key in ("commit", "pr"):
                if key in m and not is_text(m[key]):
                    self.err(f"attribution.{key}", "must be non-empty text")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle, Loader=UniqueKeyLoader)


def check_file(path, label):
    try:
        doc = load(path)
    except (OSError, yaml.YAMLError) as exc:
        return [f"{label}: does not parse: {str(exc).splitlines()[0] if str(exc) else exc}"]
    return Checker(doc, label).run()


def coverage(docs, samples_dir):
    """Checks across the samples: one per purpose and for a holding, listed in the README, documented cases covered."""
    errors = []
    label = "examples/setup-answers"
    by_kind = {}
    for name, doc in docs.items():
        org = doc.get("org") if isinstance(doc, dict) else None
        if isinstance(org, dict):
            kind = "holding" if org.get("level") == "holding" else org.get("purpose")
            by_kind.setdefault(kind, []).append(name)
    for kind in ("job", "product", "startup", "company", "personal", "holding"):
        if kind not in by_kind:
            errors.append(f"{label}: no sample for {'a holding' if kind == 'holding' else 'purpose ' + kind}")
    readme = samples_dir / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for name in docs:
        if f"[{name}]({name})" not in text:
            errors.append(f"{label}/README.md: does not list {name} (one line per file)")

    def departments(doc):
        return [d for d in (doc.get("departments") or []) if isinstance(d, dict)]

    everything = [d for d in docs.values() if isinstance(d, dict)]
    ways = {
        "a catalog entry as it is": any(d.get("from") == "catalog" and "changes" not in d for doc in everything for d in departments(doc)),
        "a catalog entry with changes": any(d.get("from") == "catalog" and "changes" in d for doc in everything for d in departments(doc)),
        "a custom department": any(d.get("from") == "custom" for doc in everything for d in departments(doc)),
        "a brought-in agent or skill": any(d.get("from") == "own" for doc in everything for d in departments(doc)),
    }
    repos = [r for doc in everything if isinstance(doc.get("repos"), list) for r in doc["repos"] if isinstance(r, dict)]
    forms = [doc.get("attribution") for doc in everything]
    cases = dict(ways)
    cases.update({
        "a deferred (`later`) answer": any("later" in repr(doc) for doc in everything),
        "a planned repo (exists: false)": any(r.get("exists") is False for r in repos),
        "a protected repo": any(r.get("protected") is True for r in repos),
        "a roadmap board": any(isinstance(doc.get("roadmap"), dict) for doc in everything),
        "attribution default": "default" in forms,
        "attribution none": "none" in forms,
        "attribution with your own text": any(isinstance(f, dict) for f in forms),
        "employer rules for a job": any(isinstance(doc.get("employer_rules"), str) and doc["employer_rules"] not in ("none", "later") for doc in everything),
        "a holding's policies repo path": any(isinstance(doc.get("policies_repo"), dict) and doc["policies_repo"].get("path") for doc in everything),
    })
    for case, covered in cases.items():
        if not covered:
            errors.append(f"{label}: no sample covers {case}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--file", help="check this one answers file only")
    args = parser.parse_args()
    errors = []
    if args.file:
        errors += check_file(Path(args.file), args.file)
        count = 1
    else:
        errors += check_file(SCHEMA_FILE, "schemas/setup-answers.yaml (example)")
        docs = {}
        paths = sorted(SAMPLES.glob("*.yaml")) if SAMPLES.is_dir() else []
        for path in paths:
            label = f"examples/setup-answers/{path.name}"
            errors += check_file(path, label)
            try:
                docs[path.name] = load(path)
            except (OSError, yaml.YAMLError):
                pass
        errors += coverage(docs, SAMPLES)
        count = 1 + len(paths)
    for error in errors:
        print(f"error: {error}")
    print(f"{count} answers file(s) checked; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
