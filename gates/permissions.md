# Permission rules from the gates

The approval gates in `org.yaml` say what the agents may do on their own. Claude Code has its own permission rules (`permissions.allow`, `ask` and `deny` in `.claude/settings.json`). This file turns the first into the second, so that Claude Code stops asking about work the gates leave free or ask to be told about (the free and notice tiers), keeps asking about work the gates hold back (the ok tier), and refuses a short list of destructive commands in every mode. Setup writes the rules (`init-fleet`, generation step 13), migration `0.14.0-to-0.15.0` adds them to an existing hq, migration `0.15.0-to-0.15.1` narrows them (section "Retired rules"), migration `0.15.1-to-0.16.0` maps the notice tier to `allow` and adds the deny baseline, and the chief of staff writes them again whenever `gates:`, `repos:`, `tracker:` or `accounts.forbidden_connectors` change (section "Write the rules again").

The rules lower the number of prompts. They are not a sandbox: a rule matches the text of a command, so it cannot see which branch a push goes to, which repo a checkout belongs to or whether a command really only reads. The written gates in `CLAUDE.md` still bind every agent, and a Claude Code prompt that the CEO approves is not the OK a gate asks for.

## How Claude Code reads the rules

Facts from the Claude Code permissions documentation that this design relies on:

- Rules are checked in the order deny, then ask, then allow, across every settings file (user, project, local): an `ask` rule in the hq's `.claude/settings.json` wins over an `allow` rule anywhere else, also in `.claude/settings.local.json`.
- An explicit `ask` rule prompts in every permission mode, auto mode included. A `deny` rule refuses in every mode. Without a rule, auto mode may run a command without a prompt when the user's own message asks for it (a headless test with Claude Code 2.1.327 ran `git reset --hard && git clean -fdx && git push --force` that way), so the only stop left is the model's own judgement: that is why the deny baseline exists.
- `Bash(gh issue list *)` matches the command with any arguments and also the bare command. A command chained with `&&`, `;` or `|` runs without a prompt only when every part is allowed.
- `*` matches any text, spaces and further arguments included, wherever it stands in the rule. A rule matches the command text, so an allow rule allows whatever its `*` stands for, and an `ask` or `deny` rule covers the usual way of writing a command, not every way (Claude Code's documentation says it is not a security boundary). Hence this file relies on an `ask` rule to take back part of an `allow` rule in two places only, the guarded wildcards of "Never allowed", and holds everything else to exact rules.
- Claude Code already runs common read-only commands without a prompt (`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, read-only `git`), and reads files inside the working folder without a prompt. These need no rule.
- `Edit(/**)` in a project settings file means every file under the folder Claude Code was started in. `Edit` rules also cover `Write`. Writes into Claude Code's protected paths, among them `.git/`, `.claude/` and files such as `.gitconfig` or `.bashrc`, ask in the default modes whatever the allow rules: Claude Code checks them before it reads the allow rules.
- Allow rules in `.claude/settings.json` apply only once the folder is trusted (the workspace trust prompt has been accepted). Ask and deny rules apply at once.
- A rule Claude Code cannot parse is skipped; the rest of the file stays in effect.
- A rule that ends in `:*` is Claude Code's older prefix form (`Bash(git pull:*)`): the text before `:*` is taken as a literal prefix, so a `*` inside it is not a wildcard. A rule that must end in a colon followed by any text ends in `:**` instead (checked with Claude Code 2.1.327: `Bash(git push * :*)` does not refuse `git push origin :old`, `Bash(git push * :**)` does).

## From tier to rule

Each rule group below lists the actions a matching command can carry out. The group's tier is the strictest tier among those actions in this org's `gates:` (`free` < `notice` < `ok`).

| Group tier | Where its rules go | Why |
|---|---|---|
| free | `allow` for a group marked `allow` under "When free"; nowhere for a group marked `ask` | The gates say "do it and mention it": no prompt, where a rule can hold the command to that action (see "Never allowed") |
| notice | the same as free | Notice means "say it in one line, then act": the line is not an OK, so Claude Code must not stop the action with a prompt. The one line is the agent's duty under the gates, not a rule |
| ok | `ask` | The CEO's explicit OK. An `ask` rule wins over every `allow` rule and prompts in every permission mode, so no allow rule anywhere can skip the prompt |

Groups marked `ask` because their commands cannot be held to one repo or to their text (issues, comments, pull-requests, tracker) keep their behaviour in every tier: nowhere for free and notice, `ask` for ok. Groups marked `guard` (see below) and `deny` do not depend on the tier.

More sources, whatever the tiers:

- **Protected repos.** For every item of `repos:` with `protected: true` (an exact repo or an owner pattern `owner/*`), the per-repo rules of every repo group go to `ask`, with that slug. A repo group whose rules already go to `ask` in their general form (below) needs no per-repo rule. A repo that is not registered gets no rule, so Claude Code asks by default.
- **Pushes in an org with a protected repo.** When any item of `repos:` has `protected: true` (an exact repo, an owner pattern or a planned repo), the push-current rules go to `ask` instead of `allow`, the hq's own push included: a push carries no repo name, so a rule cannot tell a push to a protected repo from a push to the hq, and the org is asked on every push rather than risk an unasked push where other people work. An org with no protected repo keeps them in `allow`. A repo that is not registered also counts as protected in the gates, but only a registered `protected: true` item triggers this rule: the rules cannot know about a repo the org has not listed.
- **Forbidden connectors.** Each entry of `accounts.forbidden_connectors` goes to `deny` as it is written (for example `mcp__<server>`); Claude Code accepts a server name, `mcp__<server>__*` or a single tool there.
- **The deny baseline and the guards.** The groups under "Never, in any mode" go to `deny` (and one to `ask`) in every org, whatever its gates. The groups marked `guard` go to `ask` in every org; a group marked `guard if <group>` goes to `ask` only when that group writes an `allow` rule.

And one fixed rule: `Skill(ceo-of-agents:*)` stays in `allow` (since 0.14.0), so the plugin's own procedures run without a prompt. The procedures follow the gates themselves.

No rule ever puts a group with an `ok` action in `allow`.

### Never allowed

An allow rule allows everything its `*` stands for. So no rule with a `*` goes to `allow` when the text in place of the `*` can:

- start a shell or an interpreter, or name the command to run (`sh`, `bash`, `zsh`, `env`, `xargs`, `python3`, `node`, `ruby`, `perl` and the like);
- write files (`cp`, `mv`, `rm`, `tee`, `sed` and the like);
- carry a git option that runs a program or writes a file: `-c` or `-C` before the subcommand, `--output`, `--upload-pack`, `--receive-pack`, `--exec`, `--ext-diff`, `--textconv`. A git rule with a `*` is allowed only for `status`, `add`, `commit`, `mv`, `rm`, `init`, `ls-files`, `check-ignore` and `remote add`, which take none of them; every other git command gets exact rules only (the two `git push` forms of push-current are exact: they have no `*`);
- turn a `gh` command into a write: only `gh` reads (`list`, `view`, `diff`, `checks`, `status`, `search`, `item-list`, `field-list`) take a `*`; `gh auth status` is exact, since an option of it prints the token.

**Guarded wildcards (since 0.16.0).** Two allow rules are exceptions, because the text in place of their `*` is meant to vary, and each is allowed only while its guards are in `ask` (an `ask` rule wins over `allow`):

| Allow rule | Why a `*` | Guards, always in `ask` with it |
|---|---|---|
| `Bash(gh api *)` | Any read endpoint | The rules of the group github-api-write: an explicit method, and every option that makes `gh api` send a body (which makes it a POST) |
| `Bash(gh pr merge -R <slug> *)`, for an exact slug of a registered repo that is not protected, never an owner pattern | The pull request number and merge options | The rules of the group merge-guards: `--admin` (bypasses branch protection), a second `-R` (written `-R x`, `-Rx` or `-R=x`: gh accepts all three and the last one wins), `--repo`, or a URL (a URL names its own repo and wins over `-R`) |

The guards cover the usual ways to write the same command, not every way, and are the weakest part of the design. Known gaps: a short option glued to other short options (for example `gh api -iX POST`), and anything that builds the command in a script or an alias. `scripts/ci/check_permissions.py` accepts these two rules only with their guards present in the generated `ask`, and tests the spellings above.

A group whose rules include any other such rule is marked `ask` under "When free": it never goes to `allow`, whatever its tier. `scripts/ci/check_permissions.py` in the plugin repo enforces this list for the table, for the lists it generates and for the `allowed-tools` of the plugin's skills (which get no guarded wildcard).

## Rule groups

`hq` rules are written once. `repo` rules are written once per repo: `<slug>` is the repo's `slug` from `repos:` (for an owner pattern the rule ends at the pattern, for example `Bash(gh issue create -R acme/*)`). A repo with `planned: true` gets no repo rule until it exists. `tracker` rules are written only when `tracker:` is a GitHub Project, with its `owner` and `number`.

"When free" says what the group does when its tier is free or notice: `allow` (to `allow`), `ask` (nowhere), `guard` (to `ask`, in every tier), `guard if <group>` (to `ask` when that group writes an allow rule).

| Group | Scope | Actions | When free | Rules |
|---|---|---|---|---|
| read-github | hq | `research` | allow | `Bash(gh issue list *)`, `Bash(gh issue view *)`, `Bash(gh pr list *)`, `Bash(gh pr view *)`, `Bash(gh pr diff *)`, `Bash(gh pr checks *)`, `Bash(gh repo view *)`, `Bash(gh release list *)`, `Bash(gh release view *)`, `Bash(gh run list *)`, `Bash(gh run view *)`, `Bash(gh label list *)`, `Bash(gh search issues *)`, `Bash(gh search prs *)`, `Bash(gh project view *)`, `Bash(gh project item-list *)`, `Bash(gh project field-list *)`, `Bash(gh auth status)` |
| github-api-read | hq | `research` | allow | `Bash(gh api *)` |
| sync-hq | hq | `research` | allow | `Bash(git pull)`, `Bash(git pull --ff-only)`, `Bash(git fetch)`, `Bash(git fetch origin)`, `Bash(git fetch --prune)`, `Bash(git remote)`, `Bash(git remote -v)`, `Bash(git rev-list --count HEAD)`, `Bash(date +%F)` |
| plugin-files | hq | `research` | allow | `Read(~/.claude/plugins/cache/ceo-of-agents/**)` |
| edit-hq | hq | `hq-write` | allow | `Edit(/**)` |
| commit-hq | hq | `hq-commit` | allow | `Bash(git add *)`, `Bash(git commit *)` |
| push-current | hq | `hq-commit`, `push-non-deploy-branch` | allow | `Bash(git push origin HEAD)`, `Bash(git push -u origin HEAD)` |
| issues | repo | `issues-and-labels` | ask | `Bash(gh issue create -R <slug> *)`, `Bash(gh issue edit -R <slug> *)`, `Bash(gh issue close -R <slug> *)`, `Bash(gh issue reopen -R <slug> *)`, `Bash(gh label create -R <slug> *)`, `Bash(gh label edit -R <slug> *)` |
| comments | repo | `comments` | ask | `Bash(gh issue comment -R <slug> *)`, `Bash(gh pr comment -R <slug> *)` |
| pull-requests | repo | `open-pr` | ask | `Bash(gh pr create -R <slug> *)` |
| tracker | tracker | `issues-and-labels` | ask | `Bash(gh project item-add <number> --owner <owner> *)` |
| merge | repo | `merge` | allow | `Bash(gh pr merge -R <slug> *)` |
| merge-guards | hq | `merge` | guard if merge | `Bash(gh pr merge *--admin*)`, `Bash(gh pr merge * -R*)`, `Bash(gh pr merge *--repo*)`, `Bash(gh pr merge *://*)` |
| release | hq | `deploy`, `publish` | ask | `Bash(gh release create *)`, `Bash(gh release edit *)`, `Bash(gh release upload *)`, `Bash(gh workflow run *)`, `Bash(gh run rerun *)` |
| settings | hq | `org-or-repo-settings` | ask | `Bash(gh repo create *)`, `Bash(gh repo edit *)`, `Bash(gh repo rename *)`, `Bash(gh repo archive *)`, `Bash(gh repo unarchive *)`, `Bash(gh variable *)`, `Bash(gh project create *)`, `Bash(gh project edit *)`, `Bash(gh project close *)` |
| secrets | hq | `rotate-secrets` | ask | `Bash(gh secret *)`, `Bash(gh ssh-key *)`, `Bash(gh gpg-key *)` |
| delete | hq | `delete-data` | ask | `Bash(gh issue delete *)`, `Bash(gh label delete *)`, `Bash(gh project delete *)`, `Bash(gh run delete *)`, `Bash(gh cache delete *)` |
| github-api-write | hq | `org-or-repo-settings`, `delete-data`, `merge` | guard | `Bash(gh api *-X*)`, `Bash(gh api *--method*)`, `Bash(gh api -f*)`, `Bash(gh api * -f*)`, `Bash(gh api -F*)`, `Bash(gh api * -F*)`, `Bash(gh api *--field*)`, `Bash(gh api *--raw-field*)`, `Bash(gh api *--input*)` |

The issues, comments, pull-requests and tracker groups are marked `ask`, so they never go to `allow`. With a free or notice tier their rules are written only for protected repos, to `ask`, with the slug. With an ok tier they are written once without the repo part, for every repo at once, to `ask`: `Bash(gh issue create -R <slug> *)` becomes `Bash(gh issue create *)`, and the tracker rule becomes `Bash(gh project item-add *)`. The merge group is the one repo group marked `allow`: with a free or notice tier it goes to `allow` for each registered repo that is not protected, by its exact slug (an owner pattern gets no rule, so Claude Code asks), and to `ask` for each protected repo; with an ok tier it is written once, `Bash(gh pr merge *)`, to `ask`.

Why each group is where it is:

- **read-github, github-api-read, sync-hq, plugin-files.** Reading is `research`. Reads on GitHub are free on every repo, protected ones included, so they carry no repo. `gh auth status` is exact. `git pull` and `git fetch` are listed only in their plain forms, and `git rev-list` only as `--count HEAD`, the form the session start runs: their other options can run a program or write a file. `Read(~/.claude/plugins/cache/ceo-of-agents/**)` lets the chief of staff read the plugin's schemas and migrations, which live outside the hq; reads elsewhere outside the hq still ask. The plugin's boot-set check (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"`) gets no rule, so Claude Code asks before it runs: an exact rule would have to name the plugin's install path, which differs per computer and changes with every version, and a rule for `sh` cannot have a `*`. Web search and fetch get no rule: they reach outside the org and keep Claude Code's prompt.
- **github-api-read and github-api-write.** `gh api` is a read unless it sends a method other than GET. The write guards go to `ask` in every case, even when `research` is not free or notice and no allow rule is written, so that a local `Bash(gh api *)` rule of the user's cannot let a write through unasked. They cover an explicit method (`-X`, `--method`) and the options that make `gh api` send a body, which makes it a POST (`-f`, `-F`, `--field`, `--raw-field`, `--input`). `-f` and `-F` have two rules each, because a rule `* -f*` needs a space before the option and the option may come right after `gh api`. A GraphQL read also asks: `gh api graphql` needs `-f query=...`. `--hostname` changes the host, but `gh` sends a token only to a host it has one for. A DELETE through `gh api` is refused outright (see "Never, in any mode").
- **edit-hq.** `hq-write` is editing files in the hq's working tree; `Edit(/**)` covers exactly the hq folder. Claude Code still asks for its protected paths, among them `.git/` and `.claude/`.
- **commit-hq.** A commit is `hq-commit`. `git add` and `git commit` take no option that runs a program or writes outside the repo, so they are allowed when `hq-commit` is free or notice, and ask when it is ok.
- **push-current.** The hq's own save is a commit and a push of the current branch to its `origin`. Two forms are allowed, `git push origin HEAD` and, for a new branch, `git push -u origin HEAD`: each names the remote and pushes the current branch, with no option that can run a program or change what is pushed, so they need no `*` and pass "Never allowed". A bare `git push` and `git push origin` get no rule on purpose: what they push depends on `push.default` and `remote.origin.push`, so they could push more than the current branch, or a `+` refspec, which is a force push that the deny rules cannot see. Every other form (`git push origin main`, `git push origin HEAD:other`, `git push --tags`, `git push upstream` and the like) has no allow rule, so Claude Code asks by default; the deny baseline refuses force and delete forms. Agents and skills push with `git push origin HEAD`. Limits, stated plainly: a rule cannot see the branch or the repo, so `git push origin HEAD` from a product repo checkout that deploys on push is `deploy` by the gates and still binds the agents (a prompt does not appear); protected repos cannot be told apart for `git push` either, so an org with any registered protected repo gets the two rules in `ask` instead (see "Pushes in an org with a protected repo" above); an unregistered repo does not trigger that, and there the written gate holds. An org that wants a prompt for every push moves `push-non-deploy-branch` and `hq-commit` to `ok`: the group is then written to `ask`.
- **issues, comments, pull-requests, tracker.** Free tracking writes, but marked `ask`: a rule matches the command text, and it cannot hold a write to one repo or to the text written in the command, so Claude Code asks before each. The prompt then shows the repo and the whole text. Write them with one `-R <slug>` right after the subcommand and the text inline in single quotes (`gh issue comment -R acme/app 12 --body '...'`), never with `--body-file` or `-F`: the `ask` rules of protected repos match that form. Issue and label deletes are in `delete`. Setting a Project field (`gh project item-edit`) gets no rule and asks.
- **merge and merge-guards.** Merging on a repo the org owns is `merge`: when it is free or notice, the rule is written per repo with its exact slug, so a merge on another repo is not allowed by it. Write merges as `gh pr merge -R <slug> <number> ...`, with the `-R` right after the subcommand. The guards stop the ways a second target or a bypass can ride on the `*`: `--admin` skips branch protection, a second `-R` (the guard `Bash(gh pr merge * -R*)` has a space before `-R`, so the allowed form, with `-R` right after `merge`, is not matched, and `-Rx`, `-R=x` and `-R x` later in the command are) or `--repo` changes the repo, and a pull request URL names its own repo and wins over `-R`. They are written whenever the merge group writes an allow rule. A protected repo's merge always asks. `--delete-branch` on an allowed merge deletes the remote branch of the pull request; that is part of what an allowed merge does, and the written gates cover it.
- **release, settings, secrets, delete.** One action each; in the default table all are `ok`. All are writes on GitHub, so they are marked `ask`. Repo and release deletes are in the deny baseline, not here.

## Never, in any mode

These rules are written to `deny` in every org, whatever its gates: no gate lets an agent do these without the CEO, and Claude Code refuses them in every permission mode, auto mode included. They are a backstop: the gates still bind, and a deny rule covers the usual spellings only. The CEO can run any of them by hand in a terminal outside Claude Code.

| Group | Scope | Actions | When free | Rules |
|---|---|---|---|---|
| force-push | hq | - | deny | `Bash(git push *--force*)`, `Bash(git push -f*)`, `Bash(git push * -f*)`, `Bash(git push * +*)`, `Bash(git * push *--force*)`, `Bash(git * push -f*)`, `Bash(git * push * -f*)` |
| remote-delete | hq | - | deny | `Bash(git push *--delete*)`, `Bash(git push -d*)`, `Bash(git push * -d*)`, `Bash(git push * :**)`, `Bash(git push * ':**)`, `Bash(git push * ":**)`, `Bash(git * push *--delete*)`, `Bash(git * push * :**)`, `Bash(git * push * ':**)`, `Bash(git * push * ":**)`, `Bash(git push *--mirror*)`, `Bash(git push *--prune*)` |
| history-rewrite | hq | - | deny | `Bash(git filter-branch*)`, `Bash(git filter-repo*)`, `Bash(git reflog expire*)`, `Bash(git reflog delete*)` |
| git-clean | hq | - | deny | `Bash(git clean *-*f*)`, `Bash(git clean *--force*)` |
| gh-delete | hq | - | deny | `Bash(gh repo delete*)`, `Bash(gh release delete*)` |
| api-delete | hq | - | deny | `Bash(gh api *-X DELETE*)`, `Bash(gh api *-XDELETE*)`, `Bash(gh api *--method DELETE*)`, `Bash(gh api *--method=DELETE*)`, `Bash(gh api *-X delete*)`, `Bash(gh api *-Xdelete*)`, `Bash(gh api *--method delete*)`, `Bash(gh api *--method=delete*)` |
| confirm-reset | hq | - | guard | `Bash(git reset --hard*)`, `Bash(git reset * --hard*)` |

What each covers, and why:

- **Force push.** `--force` also matches `--force-with-lease` and `--force-if-includes`. `-f` is matched at the start and after another argument. A `+` before a refspec (`git push origin +main`) forces too. The `git * push` forms cover a git option before the subcommand (`git -C repo push --force`, `git -c k=v push -f origin x`). There is no rule for `-f` inside other short flags (`-*f*`): it would also match `-u origin feature`.
- **Remote deletion.** `--delete` (also after a git option, `git -C repo push origin --delete x`), `-d`, an empty source (`git push origin :branch`, also quoted, `':branch'` and `":branch"`, and after a git option, `git -C x push origin :branch`), and `--mirror` and `--prune`, which delete remote refs that the local repo does not have.
- **History rewrites.** `git filter-branch`, `git filter-repo`, and the reflog commands that make lost commits unrecoverable.
- **`git clean` with force.** `git clean` does nothing without force. With it, it deletes untracked and ignored files, such as an hq's local-only settings, local account files and private folders, which git cannot restore. A dry run (`-n`) is not matched, unless a later word contains an `f` after a dash (a path such as `my-file`): then it is refused too. Run it by hand.
- **`gh repo delete` and `gh release delete`.** The second also covers `delete-asset`. They moved here from the delete group, which keeps the other deletes in `ask`.
- **`gh api` DELETE.** The four spellings of an explicit DELETE method, in upper and lower case.
- **`git reset --hard` asks, in every org, and is not denied.** It is the usual way out of a stuck rebase or a bad merge, so a person must be able to approve it from the prompt. It throws away uncommitted edits, which in an hq can be a department's work left for the chief of staff to commit, so it never runs without a prompt, in any mode.

Limits, stated plainly: deny rules match the usual spellings, not every one. Not caught: combined short flags such as `-uf`, a `+` refspec or a `:branch` delete written after a git option before `push` (`git -C repo push origin +main`; such a command has no allow rule, so Claude Code asks, except in auto mode, which may run it when the user's message asks for it), an alias, a script, a command built in a shell variable. They are a backstop; the gates still bind every agent.

## Retired rules

Rules that an earlier version wrote and that are no longer in the tables. "Write the rules" removes them from `allow` and `ask` like any other rule of this file:

- `Bash(sh *check-boot-set.sh*)` (0.15.0): broader than the boot-set check. No replacement: the check asks.
- `Bash(git rev-list *)` (0.15.0): broader than the count the session start runs. Replaced by `Bash(git rev-list --count HEAD)`.
- `Bash(gh auth status *)` (0.15.0): broader than the status check. Replaced by `Bash(gh auth status)`.

The allow rules that 0.15.0 wrote for the issues, comments, pull-requests and tracker groups (for example `Bash(gh issue create -R acme/app *)` or `Bash(gh project item-add 3 --owner acme *)`) leave `allow` the same way: they are rules of this file that the new lists no longer hold there.

### Retired rules (0.16.0)

- `Bash(git push *)` (0.15.0): in `ask`, it would override the exact allow rules of push-current. Replaced by those rules, the deny baseline for force and delete forms, and Claude Code's own prompt for the rest. Unlike the others it is removed from `ask` only: in `allow`, or in `.claude/settings.local.json`, it may be the user's own rule, so it stays and the CEO gets a warning (see "Write the rules").
- `Bash(gh repo delete *)` (0.15.0): in `ask`. Replaced by `Bash(gh repo delete*)` in `deny`.
- `Bash(gh release delete *)` (0.15.0): in `ask`. Replaced by `Bash(gh release delete*)` in `deny`.

The old `Bash(gh api *)` in `ask` is not a retired rule of its own: the same text is now the allow rule of github-api-read, with the guards of github-api-write in `ask`. It leaves `ask` the same way, as a rule of this file that the new `ask` list no longer holds.

## Examples

All examples use the repos `acme/app` (not protected), `acme/hq` (the hq, issues home) and `partner/site` (protected), with a Project `acme` number `3`. Every example also has the deny baseline in `deny` (the groups under "Never, in any mode", 35 rules in all) and `Bash(git reset --hard*)` and `Bash(git reset * --hard*)` in `ask`; these are not repeated below. `scripts/ci/check_permissions.py` generates each example and checks it against the exact lists.

**1. The default table** (`gates/default.md`), `merge` in `ok`:

- `allow`: `Skill(ceo-of-agents:*)`, every rule of read-github, github-api-read, sync-hq, plugin-files and commit-hq (`Bash(git add *)`, `Bash(git commit *)`), and `Edit(/**)`.
- `ask`: the two push-current rules (`Bash(git push origin HEAD)`, `Bash(git push -u origin HEAD)`: `partner/site` is protected), `Bash(gh pr merge *)`, the release, settings, secrets and delete rules, the github-api-write guards, and the issues, comments and pull-requests rules for `partner/site` (for example `Bash(gh issue comment -R partner/site *)`).
- No rule for issues, comments, pull requests and Project items on `acme/app` and `acme/hq` (marked `ask`), and no merge allow rule: Claude Code asks.

**1b. The default table with no protected repo** (only `acme/app` and `acme/hq`). As example 1, except: the two push-current rules are in `allow`, so the hq's commit and push run without a prompt, and `ask` holds no `partner/site` rule.

**2. The default table with `merge` in `notice`.** As example 1, except:

- `allow` also holds `Bash(gh pr merge -R acme/app *)` and `Bash(gh pr merge -R acme/hq *)`.
- `ask` no longer holds `Bash(gh pr merge *)`; it holds `Bash(gh pr merge -R partner/site *)` and the merge-guards: `Bash(gh pr merge *--admin*)`, `Bash(gh pr merge * -R*)`, `Bash(gh pr merge *--repo*)` and `Bash(gh pr merge *://*)`.

**3. A stricter org** that moves `issues-and-labels`, `comments`, `push-non-deploy-branch` and `hq-commit` to `ok` and `research` to `notice`:

- `allow`: `Skill(ceo-of-agents:*)`, the rules of read-github, github-api-read, sync-hq and plugin-files (notice runs without a prompt, like free), and `Edit(/**)`.
- `ask`: `Bash(git add *)`, `Bash(git commit *)` and the two push-current rules (an `ok` action always asks), `Bash(gh pr merge *)`, the release, settings, secrets and delete rules, the github-api-write guards, `Bash(gh issue create *)`, `Bash(gh issue edit *)`, `Bash(gh issue close *)`, `Bash(gh issue reopen *)`, `Bash(gh label create *)`, `Bash(gh label edit *)`, `Bash(gh issue comment *)`, `Bash(gh pr comment *)` and `Bash(gh project item-add *)`, for every repo, and `Bash(gh pr create -R partner/site *)`.

**4. Every action free** (checked by the script, not a recommended setting): as example 2, with `ask` holding only the `partner/site` rules (issues, comments, pull requests, merge), the two push-current rules (the protected repo), the merge-guards and the github-api-write guards.

## Write the rules

Merge into `.claude/settings.json`, never replace it:

1. Read `gates:`, `repos:`, `tracker:` and `accounts.forbidden_connectors` from `org.yaml`, and compute the three lists from the tables above, in table order, groups first, then repos in the order of `repos:`. The deny baseline and the guards do not depend on the gates: they are in every org's lists.
2. If `.claude/settings.json` does not exist, write `{ "permissions": { "allow": [...], "ask": [...], "deny": [...] } }`, leaving out an empty list. If it exists, keep every key (`enabledPlugins`, `attribution`, `permissions.defaultMode`, `permissions.additionalDirectories` and any other) and every rule that is not a rule of this file. A rule of this file is any rule in the tables above (the deny baseline and the guards included), with any slug, owner or number in place of `<slug>`, `<owner>` and `<number>`, or a rule of "Retired rules", in `allow`, `ask` or `deny`. One exception: the retired `Bash(git push *)` counts as a rule of this file in `ask` only. In `allow` or `deny` it may be the user's own rule, so it is never removed there.
3. In `allow`, `ask` and `deny`, remove each rule of this file that the new lists do not hold, then append each rule of the new lists that is missing, so each appears once. The exception is a forbidden connector in `deny`: it is only added, and one removed from `org.yaml` loses its deny rule by hand, through the decision that removes it.
4. Check: the file parses as JSON; every key it had before is still there; `permissions.allow` holds `Skill(ceo-of-agents:*)` once; no rule of an `ok` group, and no rule of a group marked `ask` under "When free", is in `allow`; no rule is both in `allow` and in `ask`; every guarded wildcard in `allow` (`Bash(gh api *)`, `Bash(gh pr merge -R <slug> *)`) has all its guards in `ask`; `permissions.deny` holds every rule of the baseline; no retired rule is left, except a `Bash(git push *)` in `allow` or `deny`, which stays (step 3).

`.claude/settings.local.json` (per computer, not tracked) is never written. Read it, and the `allow` list of `.claude/settings.json`, for allow rules that a new `ask` or `deny` rule overrides (the same command, for example a local `Bash(gh pr merge *)` when `merge` is `ok`), and tell the CEO in one plain line per rule that the command will ask again, or be refused; the CEO who wants it free changes the gate, through a decision. Change nothing there: these are warnings only. A `Bash(git push *)` in either place gets its own line: it lets every push form run without a prompt (the deny rules still refuse the force and delete forms they cover), so it may let through more than the gates intend, and removing it is up to the CEO.

A rule of your own that you want to keep across these writes goes into `.claude/settings.local.json`, or into `.claude/settings.json` in a form that is not in the tables.

## Write the rules again

The chief of staff runs "Write the rules" again, in the same commit, whenever one of these changes in `org.yaml`:

- `gates:` (through a decision, `record-decision`),
- `repos:` or `tracker:` (a repo or board registered, a repo protected or freed, a planned repo that now exists; the `product-repos` skill),
- `accounts.forbidden_connectors` (through a decision).

The write into `.claude/` may raise a permission prompt. If it is denied, do not work around it: say which rules are missing.
