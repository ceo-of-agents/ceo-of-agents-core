# Unreleased: the user's profile (technical or not)

Folded into the migration of the next release (see migrations/README.md). Issue: #57.

Not every user knows what a commit, a push, a pull request or an MCP server is. This change adds a profile to the hq:

- **A profile in `org.yaml`.** The new field `ceo.profile` is `technical` or `non-technical`. The setup wizard now asks one plain question for it, and the chief of staff (CoS) and the departments follow it in chat: with `non-technical`, a commit is "saved", a push is "sent to GitHub", a connector is named by its service ("Google Drive") and not by its MCP server. GitHub keeps its name for everyone. Files written in the hq keep their usual format and terms.
- **Changing it later.** The CEO asks the CoS, which records the change with `record-decision` and edits `ceo.profile`.

No schema version change: `org.yaml` stays `org/5` (`ceo.profile` is optional, absent means technical) and `company/state.md` stays `state/1`.

Apply the sections below in order. In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## Edits

### `org.yaml`

In the `ceo:` block, add this line right after the `display_name` line:

```
  profile: technical   # technical | non-technical: how the chief of staff words things in chat
```

Existing hqs default to `technical`, which is what they did until now. If the CEO has asked for plain words, propose `non-technical` instead and ask before writing it.

### `CLAUDE.md`

Section "How to talk to the CEO". After the bullet `- Report failures and your own mistakes plainly.`, add:

```
- Follow `ceo.profile` in `org.yaml`. With `non-technical`, you and the departments chat in plain words: a commit is "saved", a push "sent to GitHub", a pull request "a proposed change", a merge "accepted"; a connector is named by its service ("Google Drive"), never by its MCP server; GitHub keeps its name. Files keep their usual format and terms. The CEO can change the profile by asking: record it with `record-decision` and edit `ceo.profile`.
```

### `operating-model.md`

Section "How to start". Replace:

```
The CoS opens with a short status and the pending list. For example:
```

with:

```
The CoS opens with a short status and the pending list. If technical words get in the way, ask the CoS for plain words: it records your profile in `ceo.profile` in `org.yaml`. For example:
```

## Summary line for the CEO

Your hq now has a profile, `technical` by default. If technical words like commit or push get in the way, tell me and I will switch to plain words in chat; your files do not change.

## Check after applying

- `grep -c "^  profile: technical" org.yaml` prints 1 (or `grep -c "^  profile: non-technical" org.yaml` prints 1 if the CEO chose plain words).
- `grep -c "^- Follow \`ceo.profile\` in \`org.yaml\`" CLAUDE.md` prints 1.
- `grep -c "ask the CoS for plain words" operating-model.md` prints 1.
- `org.yaml` parses as YAML (`python3 -c "import yaml; yaml.safe_load(open('org.yaml'))"`, else `ruby -ryaml -e 'YAML.load_file(ARGV[0])' org.yaml`, else by reading).
- `git status --short` shows only `org.yaml`, `CLAUDE.md` and `operating-model.md`.
