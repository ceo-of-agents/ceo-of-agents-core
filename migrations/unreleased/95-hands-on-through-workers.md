# Unreleased: hands-on work goes through the workers

A department agent runs on a more capable model than its workers, yet the non-advisory departments held `Edit` and `Write` and wrote their own files, and the chief of staff (CoS) kept a rule to do small things itself. That put hands-on work on the expensive tier. Now every non-advisory department (catalog or custom) has `Read, Grep, Glob, Bash, Agent(reader, worker)` and no `Edit` or `Write`: it hands every file change, its dated outputs and its `inbox/` handoff included, to a `worker` that it dispatches with an explicit model one tier down. Its `Bash` stays, limited to git, gh, running tests or builds and single spot checks: never to write files (no `sed -i`, heredocs or redirects) and never to read many files (bulk reading goes to `reader`). The "Do small things yourself" rule is removed everywhere, and the CoS follows the same two rules: every file change goes to a worker or a department, and `Bash` is limited the same way.

Advisory departments (legal, finance, tax, and in a personal hq health, money, paperwork) are unchanged: they have no `Agent` tool and no `Bash`, and they keep `Edit` and `Write`. Departments brought in as they are (`from_catalog: own`) are never edited: their file lives outside the hq.

No schema version changes: `org.yaml` stays `org/5` and `company/state.md` stays `state/1`. No `org.yaml` key changes; `framework_version` is bumped by the release migration, not by this note.

Apply the sections below in order, all in one commit. In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders; where a fragment needs a rendered value, it says how to match it. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## What this changes (show the CEO before applying)

Files of the hq that change:

- `CLAUDE.md`: the Orchestration section (the department spawning bullet, the "Do small things yourself" bullet replaced by two rules) and the last sentence of "For department agents".
- `.claude/agents/<agent>.md` for each non-advisory department that comes from the catalog (`from_catalog` is `engineering`, `design-brand`, `business`, `growth-social` or `operations`, with or without `adapted: true`): its `tools:` line and its Orchestration and Outputs text.
- `.claude/agents/<agent>.md` for each custom department (`from_catalog: custom`): its `tools:` line and its Commands, Orchestration and Outputs text.
- `.claude/agents/reader.md` and `.claude/agents/worker.md`, only if one is missing.

Files that do not change: the agent files of advisory departments (`from_catalog` is `legal`, `finance`, `tax`, `health`, `money` or `paperwork`), the agent and charter of a brought-in department (`from_catalog: own`), every charter, `org.yaml`, `operating-model.md` and `company/state.md`.

Before applying, the CoS reads `departments:` in `org.yaml` and lists the concrete agent files to edit (the `agent` value of each department gives `.claude/agents/<agent>.md`), grouped as above, and shows that list to the CEO with this section.

## 1. `CLAUDE.md`

### 1.1 Orchestration: the department spawning bullet

Only when the hq has departments (the bullet that starts with `- Spawning limits: engineering may spawn` exists; skip this edit otherwise, without asking). The advisory list inside the bullet is rendered with this hq's advisory departments, so match the whole bullet from `Spawning limits: engineering may spawn` to the end of its line, and keep the list as it is. Replace:

```
Spawning limits: engineering may spawn `reader` and `worker`; other non-advisory departments may spawn `reader`. Advisory departments (<the advisory list as it is in the current bullet>) have no `Agent` tool at all; when one needs bulk reading, you dispatch a `reader` for it and pass the conclusions on. The `Agent(...)` list in an agent file names agents and is enforced only in direct `claude --agent` sessions, so a dispatched department keeps to it on its own.
```

with:

```
Spawning limits: every non-advisory department may spawn `reader` and `worker`, and has no Edit or Write tool: every file it changes goes through a `worker` it dispatches with an explicit one-tier-down model. Advisory departments (<the advisory list as it is in the current bullet>) have no `Agent` tool at all and write their own files; when one needs bulk reading, you dispatch a `reader` for it and pass the conclusions on. The `Agent(...)` list in an agent file names agents and is enforced only in direct `claude --agent` sessions, so a dispatched department keeps to it on its own.
```

### 1.2 Orchestration: the two rules that replace "Do small things yourself" (every hq)

Replace:

```
- Do small things yourself when writing the brief would cost more than doing the work.
```

with:

```
- Every file change goes to a worker or a department, hq edits that a skill prescribes included: the skill says what to write, the worker writes it, you read the diff. You keep only hq commit and push, issue and pull request writes, merges and spot reads.
- Bash, for you and for every department: only git, gh, running tests or builds and single spot checks. Never to write files (no `sed -i`, heredocs or redirects) and never to read many files (no `cat`, `sed`, `grep` or `find` sweeps): bulk reading goes to `reader`, writes go to `worker`.
```

### 1.3 "For department agents"

Only when the section exists (an hq with departments; skip otherwise, without asking). Replace:

```
At the end of your work, leave a handoff note in `inbox/` (format in `inbox/README.md`). Never commit to the hq main branch.
```

with:

```
At the end of your work, leave a handoff note in `inbox/` (format in `inbox/README.md`), written through a `worker` when your agent file gives you no Edit or Write tool. Never commit to the hq main branch.
```

## 2. Catalog departments

For each department in `org.yaml` with `from_catalog` set to one of the ids below, edit `.claude/agents/<agent>.md` as shown; skip an id the hq does not list, without asking. In these files the rendered words are the same in every fragment: `<tier words>` stands for the tier words and `<model>` for the model name that the file's existing spawn bullet already uses (the text after "Both run" or "It runs" up to "at", and the name between backticks after it). The new bullets use exactly those.

Rules for every department of this section:

- `tools:` line: replace the catalog line (shown per id) with the new one. If the current line also holds connector tools (names like `mcp__<server>__<tool>`), keep them: append them at the end of the new line, after `Agent(reader, worker)`, as they were before.
- A department with `adapted: true` keeps its "Changes for this org" section as it is. Read that section first. If it adds or drops `Bash` or `Agent`, or if the current `tools:` line differs from the catalog line in more than web abilities (`WebSearch`, `WebFetch`) and connectors, do not guess: show the CEO the section, the current line and the intended line, and ask. A web ability the CEO added or dropped stays: the new line is the new catalog line with the same web abilities added or dropped.
- Orchestration, replace the spawn bullet (shown per id) with the three bullets that follow it, and in the same section replace ` Do small things yourself when the brief would cost more than the work.` (the end of the "Verify every result" bullet) with nothing, so the bullet ends `before building on it or reporting it.`.
- Outputs, replace `Always end with an inbox handoff to the CoS (format in the charter).` with `Every file is written through a `worker`, the handoff included. Always end with an inbox handoff to the CoS (format in the charter).`

The three Orchestration bullets that replace the spawn bullet are the same for the five ids:

```
- You spawn only `reader` (read-only research and bulk reading) and `worker` (hands-on execution, every file write). Both run <tier words> at `<model>`. No other agent type.
- You have no Edit or Write tool: every file change, your dated outputs and your `inbox/` handoff included, goes to a `worker` that you dispatch with an explicit model (<tier words>, `<model>`). Read the diff before you build on it or report it.
- Bash is only for git, gh, running tests or builds and single spot checks. Never use it to write files (no `sed -i`, heredocs or redirects) or to read many files (no `cat`, `sed`, `grep` or `find` sweeps): bulk reading goes to `reader`, every file write goes to `worker`.
```

### 2.1 engineering

Only when `org.yaml` lists a department with `from_catalog: engineering` (skip otherwise, without asking). In `.claude/agents/<agent>.md` replace:

```
tools: Read, Grep, Glob, Edit, Write, Bash, Agent(reader, worker)
```

with:

```
tools: Read, Grep, Glob, Bash, Agent(reader, worker)
```

Orchestration, replace:

```
- You spawn only `reader` (read-only research and bulk reading) and `worker` (hands-on execution). Both run <tier words> at `<model>`. No other agent type.
```

with the three bullets above. Then the two edits above for the "Verify every result" bullet and the Outputs sentence.

### 2.2 design-brand

Only when `org.yaml` lists a department with `from_catalog: design-brand` (skip otherwise, without asking). In `.claude/agents/<agent>.md` replace:

```
tools: Read, Grep, Glob, Edit, Write, Agent(reader)
```

with:

```
tools: Read, Grep, Glob, Bash, Agent(reader, worker)
```

Orchestration, replace:

```
- You spawn only `reader` (read-only research and bulk reading). It runs <tier words> at `<model>`. No other agent type.
```

with the three bullets above. Then the two edits above for the "Verify every result" bullet and the Outputs sentence.

### 2.3 business

Only when `org.yaml` lists a department with `from_catalog: business` (skip otherwise, without asking). In `.claude/agents/<agent>.md` replace:

```
tools: Read, Grep, Glob, Edit, Write, WebSearch, WebFetch, Agent(reader)
```

with:

```
tools: Read, Grep, Glob, Bash, WebSearch, WebFetch, Agent(reader, worker)
```

Orchestration, replace:

```
- You spawn only `reader` (read-only research and bulk reading). It runs <tier words> at `<model>`. No other agent type.
```

with the three bullets above. Then the two edits above for the "Verify every result" bullet and the Outputs sentence.

### 2.4 growth-social

Only when `org.yaml` lists a department with `from_catalog: growth-social` (skip otherwise, without asking). In `.claude/agents/<agent>.md` replace:

```
tools: Read, Grep, Glob, Edit, Write, WebSearch, Agent(reader)
```

with:

```
tools: Read, Grep, Glob, Bash, WebSearch, Agent(reader, worker)
```

Orchestration, replace:

```
- You spawn only `reader` (read-only research and bulk reading). It runs <tier words> at `<model>`. No other agent type.
```

with the three bullets above. Then the two edits above for the "Verify every result" bullet and the Outputs sentence.

### 2.5 operations

Only when `org.yaml` lists a department with `from_catalog: operations` (skip otherwise, without asking). In `.claude/agents/<agent>.md` replace:

```
tools: Read, Grep, Glob, Edit, Write, Agent(reader)
```

with:

```
tools: Read, Grep, Glob, Bash, Agent(reader, worker)
```

Orchestration, replace:

```
- You spawn only `reader` (read-only research and bulk reading). It runs <tier words> at `<model>`. No other agent type.
```

with the three bullets above. Then the two edits above for the "Verify every result" bullet and the Outputs sentence.

## 3. Custom departments

Only when `org.yaml` lists a department with `from_catalog: custom` (skip otherwise, without asking). For each one, edit `.claude/agents/<agent>.md`. In this file `<department model>`, `<tier words>` and `<worker model>` stand for the three rendered values already in its Orchestration paragraph (the model after "You run on", and the tier words and the model name in backticks after "the `reader` agent"); the new paragraph uses exactly those. `<id>` is the department's `id`.

### 3.1 `tools:` line

Replace the line that starts with `tools:` (before: `Read, Grep, Glob, Edit, Write, Agent(reader)`, or `Read, Grep, Glob, Edit, Write, Bash, Agent(reader)` when the CEO had allowed commands) with:

```
tools: Read, Grep, Glob, Bash, Agent(reader, worker)
```

If the current line also holds connector tools (names like `mcp__<server>__<tool>`), keep them at the end of the new line, after `Agent(reader, worker)`.

### 3.2 Commands

Section `## Commands`. Its body is one sentence, either `You do not run commands (you have no `Bash` tool).` or `You may run commands (scripts, command-line tools, git) for: <the CEO's reason>. Never commit to or push the hq main branch.` Replace that sentence, whichever it is, with:

```
Bash is only for git, gh, running tests or builds and single spot checks. Never use it to write files (no `sed -i`, heredocs or redirects) or to read many files (no `cat`, `sed`, `grep` or `find` sweeps): bulk reading goes to `reader`, every file write goes to `worker`. Never commit to or push the hq main branch.
```

A reason the CEO gave for commands is not kept in the file (it stays in the decision record of that department's creation).

### 3.3 Orchestration paragraph

Section `## Orchestration`. Replace the paragraph from `You run on` to its last sentence (`Do small tasks yourself when writing the brief would cost more than the work.`) with:

```
You run on <department model> as an orchestrator. Plan, decide and judge yourself. Delegate bulk reading and long research to the `reader` agent and every file write to the `worker` agent, both <tier words> (`<worker model>`). You have no Edit or Write tool: every file change, your dated outputs and your `inbox/` handoff included, goes to a `worker` that you dispatch with an explicit model (<tier words>, `<worker model>`). Read the diff before you build on it or report it. You spawn only `reader` and `worker` and no other type. Set the model explicitly on every spawn. Never escalate to a more capable model than your own, and never hand work back up to the CoS. Give each reader and worker a self-contained brief: goal, files, constraints, definition of done, what to return. End each brief with: "If you spawn sub-agents, do not set a more capable model than your own." Run independent readers and workers in parallel. Verify each result before using it.
```

### 3.4 Known limit

In the sentence that starts `Known limit:`, replace:

```
so you must still spawn only `reader`.
```

with:

```
so you must still spawn only `reader` and `worker`.
```

### 3.5 Outputs, first bullet

Section `## Outputs`. In the first bullet, replace:

```
as dated files, or as drafts, as the charter says.
```

with:

```
as dated files, or as drafts, as the charter says. Every file, the dated results and the handoff note included, is written through a `worker`.
```

## 4. Advisory and brought-in departments: no change

- Advisory departments (`from_catalog` is `legal`, `finance`, `tax`, `health`, `money` or `paperwork`): their agent files do not change. They keep `Edit` and `Write` and have no `Agent` and no `Bash`.
- Brought-in departments (`from_catalog: own`): the agent or skill lives outside the hq and is never edited here. Their charter does not change.

## 5. The generic workers

If `.claude/agents/reader.md` or `.claude/agents/worker.md` is missing (an hq that skipped them), create the missing file by rendering `${CLAUDE_PLUGIN_ROOT}/templates/workers/<name>.md` (`reader.md` or `worker.md`). The only placeholders are `{{ORG_NAME}}` and `{{MODEL_WORKERS}}`:

- `{{ORG_NAME}}`: `org.name` in `org.yaml`.
- `{{MODEL_WORKERS}}`: the model the Orchestration section of `CLAUDE.md` names for the CoS's own workers, in the phrase `your own workers run on **<model>**`. If a department has `workers: same` in `org.yaml`, that does not change these two files: they stay on the CoS workers' model.

Both files are needed now: every non-advisory department spawns `worker` for its file writes. If a file already exists, leave it as it is.

## 6. Plugin-only changes (no hq edit)

- The setup wizard and the `departments` skill no longer ask whether a custom department runs commands: a custom department always gets `Read, Grep, Glob, Bash, Agent(reader, worker)`.
- `commands` in a setup answers file (`schemas/setup-answers.yaml`) is deprecated: it is accepted and ignored (when present its shape is still checked).
- On a catalog department, only `WebSearch` and `WebFetch` can be added or dropped; `Bash` and `Agent(reader, worker)` are fixed for non-advisory departments, and an advisory one never gains them.
- `docs/design.md`, `catalog/README.md` and the example answers files are updated.

## Summary for the CEO

"From now on your departments hand every file change to the cheaper helper instead of writing it themselves, and so do I. They can still run a few simple commands themselves, such as saving to git or running tests. Departments that only give advice are unchanged, and so are any agents you brought in yourself."

## Check after applying

- `grep -c "Do small things yourself" CLAUDE.md` prints 0, and `grep -c "^- Every file change goes to a worker or a department" CLAUDE.md` and `grep -c "^- Bash, for you and for every department" CLAUDE.md` each print 1.
- In an hq with departments: `grep -c "^- Spawning limits: every non-advisory department may spawn" CLAUDE.md` prints 1 and `grep -c "written through a \`worker\` when your agent file gives you no Edit or Write tool" CLAUDE.md` prints 1.
- Take the agent files of the non-advisory departments (catalog and custom, listed before applying) as `<files>`. `grep -l -E "^tools: .*\b(Edit|Write)\b" <files>` prints nothing. `grep -L -E "^tools: .*\bBash\b.*Agent\(reader, worker\)" <files>` prints nothing. `grep -l -E "Do small (things|tasks) yourself" <files>` prints nothing. `grep -L "every file write" <files>` prints nothing (each Orchestration or Commands text names it).
- A custom department's file has `Never commit to or push the hq main branch.` in `## Commands` and `spawn only \`reader\` and \`worker\`` in Orchestration and Known limit.
- The advisory agent files and the brought-in departments' charters are unchanged: `git diff --stat` shows none of them.
- `.claude/agents/reader.md` and `.claude/agents/worker.md` exist, and their `model:` equals the model named for the CoS's own workers in `CLAUDE.md`.
- Every `.claude/agents/*.md` frontmatter parses as YAML: `python3 -c "import sys, yaml; [yaml.safe_load(open(f).read().split('---')[1]) for f in sys.argv[1:]]" .claude/agents/*.md` prints nothing (else `ruby -ryaml -e 'ARGV.each { |f| YAML.safe_load(File.read(f).split("---")[1]) }' .claude/agents/*.md`, else by reading).
- `git status --short` lists only the expected files: `CLAUDE.md`, the non-advisory department agent files, and a worker file only if it was missing.
- `sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"` ends with `verdict: ok`, or reports no new issue from these lines: `CLAUDE.md` grows by about 0.6 KiB and must stay at most 24,576 bytes (`schemas/boot-set.md`).
