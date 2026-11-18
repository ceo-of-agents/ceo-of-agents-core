# Permission rules from the gates

The approval gates in `org.yaml` say what the agents may do on their own. Claude Code has its own permission rules (`permissions.allow`, `ask` and `deny` in `.claude/settings.json`). This file turns the first into the second, so that Claude Code stops asking about work the gates leave free, and keeps asking about work the gates hold back. Setup writes the rules (`init-fleet`, generation step 13), migration `0.14.0-to-0.15.0` adds them to an existing hq, migration `0.15.0-to-0.15.1` removes the retired rules (section "Retired rules"), and the chief of staff writes them again whenever `gates:`, `repos:`, `tracker:` or `accounts.forbidden_connectors` change (section "Write the rules again").

The rules lower the number of prompts. They are not a sandbox: a rule matches the start of a command, so it cannot see which branch a push goes to or whether a command really only reads. The written gates in `CLAUDE.md` still bind every agent, and a Claude Code prompt that the CEO approves is not the OK a gate asks for.

## How Claude Code reads the rules

Facts from the Claude Code permissions documentation that this design relies on:

- Rules are checked in the order deny, then ask, then allow, across every settings file (user, project, local): an `ask` rule in the hq's `.claude/settings.json` wins over an `allow` rule anywhere else, also in `.claude/settings.local.json`.
- `Bash(gh issue list *)` matches the command with any arguments and also the bare command. A command chained with `&&`, `;` or `|` runs without a prompt only when every part is allowed.
- `*` matches any sequence of characters, spaces and further arguments included, wherever it stands in the rule: `Bash(sh *check.sh*)` matches every `sh` command whose text contains `check.sh`, whatever else it runs.
- Claude Code already runs common read-only commands without a prompt (`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, read-only `git`), and reads files inside the working folder without a prompt. These need no rule.
- `Edit(/**)` in a project settings file means every file under the folder Claude Code was started in. `Edit` rules also cover `Write`. Writes into `.claude/` always ask, whatever the rules.
- Allow rules in `.claude/settings.json` apply only once the folder is trusted (the workspace trust prompt has been accepted). Ask and deny rules apply at once.
- A rule Claude Code cannot parse is skipped; the rest of the file stays in effect.

## From tier to rule

Each rule group below lists the actions a matching command can carry out. The group's tier is the strictest tier among those actions in this org's `gates:` (`free` < `notice` < `ok`).

| Group tier | Where its rules go | Why |
|---|---|---|
| free | `allow` | The gates say "do it and mention it": no prompt |
| notice | nowhere | Claude Code asks by default. The CEO may allow such a command in `.claude/settings.local.json` (for example "Always allow" in a prompt), since notice means "say it, then act" |
| ok | `ask` | The CEO's explicit OK. An `ask` rule wins over every `allow` rule, so no allow rule anywhere can skip the prompt |

Two more sources, whatever the tiers:

- **Protected repos.** For every item of `repos:` with `protected: true` (an exact repo or an owner pattern `owner/*`), the per-repo rules of every repo group go to `ask`, with that slug. A repo group whose rules already go to `ask` in their general form (below) needs no per-repo rule. An exact protected repo under an unprotected owner pattern is then asked, because `ask` wins over the pattern's `allow`. A repo that is not registered gets no rule, so Claude Code asks by default.
- **Forbidden connectors.** Each entry of `accounts.forbidden_connectors` goes to `deny` as it is written (for example `mcp__<server>`); Claude Code accepts a server name, `mcp__<server>__*` or a single tool there.

And one fixed rule: `Skill(ceo-of-agents:*)` stays in `allow` (since 0.14.0), so the plugin's own procedures run without a prompt. The procedures follow the gates themselves.

No rule ever puts a group with an `ok` action in `allow`.

No rule puts a wildcard in a command that starts a shell or an interpreter (`sh`, `bash`, `zsh`, `env`, `python3`, `node`, `ruby` and the like): any such rule lets that program run any code. A command whose options can run a program or write a file (for example `git rev-list --output=<file>`) gets only exact rules, in the form the skills use. `scripts/ci/check_permissions.py` fails on a wildcard shell or interpreter rule, here and in the `allowed-tools` of the plugin's skills.

## Rule groups

`hq` rules are written once. `repo` rules are written once per repo: `<slug>` is the repo's `slug` from `repos:` (for an owner pattern the rule ends at the pattern, for example `Bash(gh issue create -R acme/*)`). A repo with `planned: true` gets no repo rule until it exists. `tracker` rules are written only when `tracker:` is a GitHub Project, with its `owner` and `number`.

| Group | Scope | Actions | Rules |
|---|---|---|---|
| read-github | hq | `research` | `Bash(gh issue list *)`, `Bash(gh issue view *)`, `Bash(gh pr list *)`, `Bash(gh pr view *)`, `Bash(gh pr diff *)`, `Bash(gh pr checks *)`, `Bash(gh repo view *)`, `Bash(gh release list *)`, `Bash(gh release view *)`, `Bash(gh run list *)`, `Bash(gh run view *)`, `Bash(gh label list *)`, `Bash(gh search issues *)`, `Bash(gh search prs *)`, `Bash(gh project view *)`, `Bash(gh project item-list *)`, `Bash(gh project field-list *)`, `Bash(gh auth status *)` |
| sync-hq | hq | `research` | `Bash(git pull)`, `Bash(git pull --ff-only)`, `Bash(git fetch)`, `Bash(git fetch origin)`, `Bash(git fetch --prune)`, `Bash(git remote)`, `Bash(git remote -v)`, `Bash(git rev-list --count HEAD)`, `Bash(date +%F)` |
| plugin-files | hq | `research` | `Read(~/.claude/plugins/cache/ceo-of-agents/**)` |
| edit-hq | hq | `hq-write` | `Edit(/**)` |
| commit-hq | hq | `hq-commit` | `Bash(git add *)`, `Bash(git commit *)` |
| issues | repo | `issues-and-labels` | `Bash(gh issue create -R <slug> *)`, `Bash(gh issue edit -R <slug> *)`, `Bash(gh issue close -R <slug> *)`, `Bash(gh issue reopen -R <slug> *)`, `Bash(gh label create -R <slug> *)`, `Bash(gh label edit -R <slug> *)` |
| comments | repo | `comments` | `Bash(gh issue comment -R <slug> *)`, `Bash(gh pr comment -R <slug> *)` |
| pull-requests | repo | `open-pr` | `Bash(gh pr create -R <slug> *)` |
| tracker | tracker | `issues-and-labels` | `Bash(gh project item-add <number> --owner <owner> *)` |
| push | hq | `push-non-deploy-branch`, `hq-commit`, `deploy` | `Bash(git push *)` |
| merge | hq | `merge` | `Bash(gh pr merge *)` |
| release | hq | `deploy`, `publish` | `Bash(gh release create *)`, `Bash(gh release edit *)`, `Bash(gh release upload *)`, `Bash(gh workflow run *)`, `Bash(gh run rerun *)` |
| settings | hq | `org-or-repo-settings` | `Bash(gh repo create *)`, `Bash(gh repo edit *)`, `Bash(gh repo rename *)`, `Bash(gh repo archive *)`, `Bash(gh repo unarchive *)`, `Bash(gh variable *)`, `Bash(gh project create *)`, `Bash(gh project edit *)`, `Bash(gh project close *)` |
| secrets | hq | `rotate-secrets` | `Bash(gh secret *)`, `Bash(gh ssh-key *)`, `Bash(gh gpg-key *)` |
| delete | hq | `delete-data` | `Bash(gh repo delete *)`, `Bash(gh release delete *)`, `Bash(gh issue delete *)`, `Bash(gh label delete *)`, `Bash(gh project delete *)`, `Bash(gh run delete *)`, `Bash(gh cache delete *)` |
| github-api | hq | `org-or-repo-settings`, `delete-data`, `merge` | `Bash(gh api *)` |

When a repo group's tier is not free, its rules are written once without the repo part, for every repo at once: `Bash(gh issue create -R <slug> *)` becomes `Bash(gh issue create *)` (and `ask` for an ok tier, nothing for a notice tier). The tracker rule likewise becomes `Bash(gh project item-add *)`.

Why each group is where it is:

- **read-github, sync-hq, plugin-files.** Reading is `research`. Reads on GitHub are free on every repo, protected ones included, so they carry no repo. `git pull` and `git fetch` are listed only in their plain forms: options such as `--upload-pack` can run a program. `git rev-list` is listed only as `--count HEAD`, the form the session start runs: its `--output` option writes a file. `Read(~/.claude/plugins/cache/ceo-of-agents/**)` lets the chief of staff read the plugin's schemas and migrations, which live outside the hq; reads elsewhere outside the hq still ask. The plugin's boot-set check (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"`) gets no rule, so Claude Code asks before it runs: an exact rule would have to name the plugin's install path, which differs per computer and changes with every version, and a rule with a wildcard would let any `sh` command through. Web search and fetch get no rule: they reach outside the org and keep Claude Code's prompt.
- **edit-hq.** `hq-write` is editing files in the hq's working tree; `Edit(/**)` covers exactly the hq folder (Claude Code still asks for `.claude/`).
- **commit-hq.** A commit is `hq-commit`. In the default table it is notice, so it gets no rule: Claude Code asks, and the CEO may allow it on this computer. The skills that commit also allow `git add` and `git commit` while they run.
- **issues, comments, pull-requests, tracker.** Free tracking writes, scoped to one registered repo through `-R <slug>` right after the subcommand (`gh issue comment -R acme/app 12 --body "..."`). A command without `-R`, or with a repo that is not registered, gets no rule and asks. Issue and label deletes are in `delete`. Setting a Project field (`gh project item-edit`) names the project by an id the setup cannot know, so it keeps its prompt.
- **push.** One rule cannot tell a work branch from a branch that deploys, or from the hq's main branch, so `git push` takes the strictest of the three actions.
- **merge, release, settings, secrets, delete.** One action each; in the default table all are `ok`.
- **github-api.** `gh api` can read or change anything on GitHub, and its method can be set anywhere in the command, so it takes the strictest action it can reach.

## Retired rules

Rules that an earlier version wrote and that are no longer in the tables. "Write the rules" removes them from `allow` and `ask` like any other rule of this file:

- `Bash(sh *check-boot-set.sh*)` (0.15.0): the wildcard matched any `sh` command that names the script, so it allowed any shell command.
- `Bash(git rev-list *)` (0.15.0): `git rev-list --output=<file>` writes a file anywhere. Replaced by `Bash(git rev-list --count HEAD)`.

## Examples

The default table (`gates/default.md`) and the repos `acme/app` (not protected), `acme/hq` (the hq, issues home) and `partner/site` (protected), with a Project `acme` number `3`:

- `allow`: `Skill(ceo-of-agents:*)`, every rule of read-github, sync-hq and plugin-files, `Edit(/**)`, the issues, comments and pull-requests rules for `acme/app` and `acme/hq` (for example `Bash(gh issue create -R acme/app *)`), and `Bash(gh project item-add 3 --owner acme *)`.
- `ask`: the push, merge, release, settings, secrets, delete and github-api rules, and the issues, comments and pull-requests rules for `partner/site` (for example `Bash(gh issue comment -R partner/site *)`).
- No rule for `git add` and `git commit` (notice): Claude Code asks.

A stricter org that moves `issues-and-labels` and `comments` to `ok` and `research` to `notice`, with the same repos:

- `allow`: `Skill(ceo-of-agents:*)`, `Edit(/**)`, `Bash(gh pr create -R acme/app *)` and `Bash(gh pr create -R acme/hq *)`.
- `ask`: the push, merge, release, settings, secrets, delete and github-api rules, plus `Bash(gh issue create *)`, `Bash(gh issue edit *)`, `Bash(gh issue close *)`, `Bash(gh issue reopen *)`, `Bash(gh label create *)`, `Bash(gh label edit *)`, `Bash(gh issue comment *)`, `Bash(gh pr comment *)` and `Bash(gh project item-add *)`, for every repo, and `Bash(gh pr create -R partner/site *)`.
- No rule for the reads on GitHub, `git pull` or the plugin files: Claude Code asks before each.

The exact lists for both examples are checked by `scripts/ci/check_permissions.py` in the plugin repo.

## Write the rules

Merge into `.claude/settings.json`, never replace it:

1. Read `gates:`, `repos:`, `tracker:` and `accounts.forbidden_connectors` from `org.yaml`, and compute the three lists from the tables above, in table order, groups first, then repos in the order of `repos:`.
2. If `.claude/settings.json` does not exist, write `{ "permissions": { "allow": [...], "ask": [...], "deny": [...] } }`, leaving out an empty list. If it exists, keep every key (`enabledPlugins`, `attribution`, `permissions.defaultMode`, `permissions.additionalDirectories` and any other) and every rule that is not a rule of this file. A rule of this file is any rule in the tables above, with any slug, owner or number in place of `<slug>`, `<owner>` and `<number>`, or a rule of "Retired rules", in `allow` or `ask`.
3. In `allow` and `ask`, remove each rule of this file that the new lists do not hold, then append each rule of the new lists that is missing, so each appears once. In `deny`, only add: a forbidden connector removed from `org.yaml` loses its deny rule by hand, through the decision that removes it.
4. Check: the file parses as JSON; every key it had before is still there; `permissions.allow` holds `Skill(ceo-of-agents:*)` once; no rule of an `ok` group is in `allow`; no rule is both in `allow` and in `ask`; no retired rule is left.

`.claude/settings.local.json` (per computer, not tracked) is never written. Read it, and the `allow` list of `.claude/settings.json`, for allow rules that a new `ask` rule overrides (the same command, for example a local `Bash(gh pr merge *)` when `merge` is `ok`), and tell the CEO in one plain line per rule that the command will ask again; the CEO who wants it free changes the gate, through a decision.

A rule of your own that you want to keep across these writes goes into `.claude/settings.local.json`, or into `.claude/settings.json` in a form that is not in the tables.

## Write the rules again

The chief of staff runs "Write the rules" again, in the same commit, whenever one of these changes in `org.yaml`:

- `gates:` (through a decision, `record-decision`),
- `repos:` or `tracker:` (a repo or board registered, a repo protected or freed, a planned repo that now exists; the `product-repos` skill),
- `accounts.forbidden_connectors` (through a decision).

The write into `.claude/` may raise a permission prompt. If it is denied, do not work around it: say which rules are missing.
