#!/usr/bin/env python3
"""Check the tips file.

Validates tips/tips.yaml against the rules of schemas/tips.md: the schema line,
the fields of each tip (id, since, pending, depends_on, when, text, phrase,
translations), the condition keys and their value shapes, the placeholders, and
that `since` is not higher than the plugin version. It also runs a few
behaviour tests on its own rules. With --file <path> it checks that one file
only (and skips the behaviour tests).
Needs PyYAML.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TIPS_FILE = ROOT / "tips" / "tips.yaml"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"

ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
LANG_RE = re.compile(r"^[a-z]{2}$")
PLACEHOLDER_RE = re.compile(r"\{([^{}]*)\}")
TIP_KEYS = {"id", "since", "pending", "depends_on", "when", "text", "phrase", "translations"}
WHEN_KEYS = {"pending", "days_since_last_session", "days_since_last_brief", "hq_behind_plugin", "file_missing", "chat"}
PLACEHOLDERS = {"codes", "decision_code", "cos_name", "department", "initiative", "repo"}
KINDS = {"ok", "do", "decide"}
SIGNALS = {"hesitant-question", "vague-request", "recurring-topic", "personal-todo", "outside-departments"}


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def version_tuple(text):
    return tuple(int(part) for part in text.split("."))


def plugin_version():
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def check_min(where, value, errors):
    if not (isinstance(value, dict) and set(value) == {"min"} and is_int(value["min"]) and value["min"] > 0):
        errors.append(f"{where}: must be {{min: <positive integer>}}")


def check_when(where, when, errors):
    if not isinstance(when, dict) or not when:
        errors.append(f"{where}: when must be a non-empty mapping")
        return
    for key, value in when.items():
        at = f"{where}: when.{key}"
        if key not in WHEN_KEYS:
            errors.append(f"{at}: unknown condition key (known: {', '.join(sorted(WHEN_KEYS))})")
        elif key == "pending":
            ok = (isinstance(value, dict) and set(value) == {"kind", "min"} and value["kind"] in KINDS
                  and is_int(value["min"]) and value["min"] > 0)
            if not ok:
                errors.append(f"{at}: must be {{kind: ok|do|decide, min: <positive integer>}}")
        elif key in ("days_since_last_session", "days_since_last_brief"):
            check_min(at, value, errors)
        elif key == "hq_behind_plugin":
            if value is not True:
                errors.append(f"{at}: must be true")
        elif key == "file_missing":
            if not is_text(value) or value.startswith("/") or ".." in Path(value).parts:
                errors.append(f"{at}: must be a relative path without '..'")
        elif key == "chat":
            if value not in SIGNALS:
                errors.append(f"{at}: must be one of {', '.join(sorted(SIGNALS))}")


def placeholders(text):
    return set(PLACEHOLDER_RE.findall(text))


def check_tip(index, tip, seen, current, errors):
    if not isinstance(tip, dict):
        errors.append(f"tips[{index}]: must be a mapping")
        return
    tid = tip.get("id")
    where = f"tip {tid!r}" if isinstance(tid, str) else f"tips[{index}]"
    if not isinstance(tid, str) or not ID_RE.match(tid):
        errors.append(f"{where}: id must match ^[a-z][a-z0-9-]*$")
    elif tid in seen:
        errors.append(f"{where}: duplicate id")
    else:
        seen.add(tid)
    for key in sorted(set(tip) - TIP_KEYS):
        errors.append(f"{where}: unknown key {key!r}")
    for key in ("text", "phrase"):
        if not is_text(tip.get(key)):
            errors.append(f"{where}: {key} must be a non-empty string")
    pending = tip.get("pending")
    if "pending" in tip and pending is not True:
        errors.append(f"{where}: pending, when present, must be true")
    if "since" in tip:
        since = tip["since"]
        if not isinstance(since, str) or not VERSION_RE.match(since):
            errors.append(f"{where}: since must be a quoted X.Y.Z string")
        elif pending is True:
            errors.append(f"{where}: a pending tip has no since")
        elif version_tuple(since) > version_tuple(current):
            errors.append(f"{where}: since {since} is higher than the plugin version {current}")
    elif pending is not True:
        errors.append(f"{where}: since is required unless pending is true")
    if "depends_on" in tip:
        if pending is not True:
            errors.append(f"{where}: depends_on is allowed only with pending: true")
        if not is_int(tip["depends_on"]) or tip["depends_on"] <= 0:
            errors.append(f"{where}: depends_on must be an issue number")
    check_when(where, tip.get("when"), errors)
    texts = {key: tip[key] for key in ("text", "phrase") if is_text(tip.get(key))}
    source = set()
    for text in texts.values():
        source |= placeholders(text)
    for name in sorted(source - PLACEHOLDERS):
        errors.append(f"{where}: unknown placeholder {{{name}}}")
    if "codes" in source and not (isinstance(tip.get("when"), dict) and "pending" in tip["when"]):
        errors.append(f"{where}: {{codes}} needs a pending condition in when")
    translations = tip.get("translations")
    if translations is None:
        return
    if not isinstance(translations, dict):
        errors.append(f"{where}: translations must be a mapping")
        return
    for lang, entry in translations.items():
        at = f"{where}: translations.{lang}"
        if not isinstance(lang, str) or not LANG_RE.match(lang):
            errors.append(f"{at}: key must be a 2-letter lowercase language code")
        if not (isinstance(entry, dict) and set(entry) == {"text", "phrase"} and is_text(entry["text"]) and is_text(entry["phrase"])):
            errors.append(f"{at}: must hold exactly text and phrase, both non-empty strings")
            continue
        for key in ("text", "phrase"):
            if key in texts and placeholders(entry[key]) != placeholders(tip[key]):
                errors.append(f"{at}: {key} must carry the same placeholders as the source")


def check_data(data, current):
    errors = []
    if not isinstance(data, dict):
        return ["the file must be a mapping with schema and tips"]
    if data.get("schema") != "tips/1":
        errors.append('schema must be exactly "tips/1"')
    tips = data.get("tips")
    if not isinstance(tips, list) or not tips:
        errors.append("tips must be a non-empty list")
        return errors
    seen = set()
    for index, tip in enumerate(tips):
        check_tip(index, tip, seen, current, errors)
    return errors


def check_file(path, current):
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{path}: cannot read: {exc}"]
    return check_data(data, current)


def behaviour(current):
    """The rules above must accept a good tip and reject each bad one."""
    errors = []
    good = {"id": "a-tip", "since": "0.1.0", "when": {"pending": {"kind": "ok", "min": 2}},
            "text": "Text {codes}", "phrase": "Approve {codes}"}

    def make(**changes):
        tip = {**good, **changes}
        return {"schema": "tips/1", "tips": [{k: v for k, v in tip.items() if v is not None}]}

    if check_data(make(), current):
        errors.append("self-test: a valid tip was rejected")
    bad = {
        "unquoted since": make(since=0.1),
        "since above the plugin version": make(since="99.0.0"),
        "missing since": make(since=None),
        "pending with since": make(pending=True),
        "depends_on without pending": make(depends_on=5),
        "unknown placeholder": make(phrase="Say {nothing}"),
        "codes without a pending condition": make(when={"chat": "vague-request"}),
        "unknown condition key": make(when={"moon": True}),
        "path with ..": make(when={"file_missing": "../x"}),
        "translation with other placeholders": make(translations={"it": {"text": "Testo", "phrase": "Approva"}}),
    }
    for name, data in bad.items():
        if not check_data(data, current):
            errors.append(f"self-test: not reported: {name}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--file", help="check this file only (skips the behaviour tests)")
    args = parser.parse_args()
    current = plugin_version()
    errors = check_file(args.file or TIPS_FILE, current)
    if not args.file:
        errors += behaviour(current)
    for error in errors:
        print(f"error: {error}")
    print(f"tips file checked; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
