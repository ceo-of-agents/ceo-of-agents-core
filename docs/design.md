# ceo-of-agents: design spec (draft v0)

Status: v0.23.0 implemented. v0.1.1 implemented phase 0 plus review fixes. Sections updated where implementation diverged. v0.1.1 applied these fixes: restricted spawning with `reader` and `worker` agents, read-only connectors for advisory departments, a separate policies repo, a portfolio brief that never pulls, no preselected choices in the wizard, an optional hq remote, and fully filled custom departments. v0.2.0 adds schema `org/2`: the chief of staff's name (`cos.display_name`) and the fleet purpose (`org.purpose`: job, product, startup, company), which drives suggested departments, account rules and holding eligibility. v0.3.0 renames the setup wizard to `init-fleet`, the only command the CEO types; the four CoS procedures (`intake`, `record-decision`, `weekly-brief`, `portfolio-brief`) are hidden from the `/` menu (`user-invocable: false`) and invoked by the CoS from plain-language requests. Custom departments get the same purpose-aware account-separation line as catalog departments. v0.4.0 adds three working rules: a department review in `init-fleet` with a one-line reason for every elevated grant (also when a department is added later), task-splitting rules for the CoS, and blocked and failure hygiene for workers and departments. v0.5.0 makes the wizard ask what the org is about (generating `company/vision.md` and `company/strategy.md`), rewrites the gates question in plain language, drops the connectors question (every department starts with none; the CoS checks connectors of other accounts at the first session and writes them to an untracked `accounts.local.yaml`), and makes every CoS procedure check for a remote before pulling. v0.6.0 adds schema `org/3`: a registry of the org's product repos (`repos:`, GitHub slug, role, visibility, issues home; local clone paths per machine in `accounts.local.yaml`) and an optional roadmap tracker (`tracker:`, a GitHub Project). A standing rule in `CLAUDE.md` makes every change check and update the tracker and its issues; those writes are free. `intake` gains an issue route, `record-decision` creates and updates issues and Project fields, `weekly-brief` reads the tracker, issues and PRs read-only, and engineering carries tracker hygiene. No hooks or schedules: the rules run when a session runs. v0.7.0 adds schema `org/4`: each department has an agent name (`agent`), its persona in lowercase or its id, which names its agent file and is used to route and to open it directly; the department id stays the key for charters, cards and handoffs. A hidden skill, `hq-version`, checks the hq's framework version at every session start and applies migrations only after the CEO's OK. v0.8.0 drops the CoS's first-session question about connectors of other accounts: no per-computer forbidden-connector list and no deny rules written by the CoS. `accounts.local.yaml` now holds only local clone paths (`repo_paths`). The written account-separation rule stays, every department still starts with no connectors, and `accounts.forbidden_connectors` in `org.yaml` stays an optional list filled through a decision. v0.8.1 makes one install the supported setup: one copy of the plugin at project scope, in the hq folder. A second copy at another scope could stay on an older version and be the one loaded; the README says how to check and remove it, and `hq-version` points to it when the hq is newer than the loaded plugin. v0.9.0 changes the wizard and the generated hq: chat language is asked first, multi-line answers are kept verbatim, custom departments are asked whether they need to run commands, an `attribution` setting (in `.claude/settings.json`) controls how commits and pull requests are signed, a repo can be recorded as not yet existing (`planned: true`) with an action item to create it, optional questions can be answered "later" and become action items, a department can be set to top model with workers on the same tier (`workers: same`), and a holding CoS lists the pending items of its registered companies at session start. v0.10.0 adds the fleet purpose `personal`, with three advisory catalog entries (health, money, paperwork) and a git-ignored `private/` folder for personal data. v0.11.0 adds schema `org/5` and five changes. A leaner hq: the start-of-session routine, the department and grant steps and the product repos procedures move from `CLAUDE.md` into hidden skills (`session-start`, `departments`, `product-repos`), the files read at every session start get a size budget checked at session start, and analyses and notes get lifecycle frontmatter with an `archive/` folder that default searches skip. Protected repos: every repo in `repos:` declares `protected`, and on a protected repo every write needs the CEO's OK; the hq is never protected. Four ways to build the org (catalog as is, catalog plus changes, custom, or the CEO's own agents and skills), with an overlap check that only warns. An opt-in, read-only reading of the services the CEO marks as this org's to pre-fill setup, granting nothing. Design and brand is suggested for job, product, startup and company, with the org chart as its first task, and clone paths are proposed next to the hq, never inside it. v0.12.0 finishes the lean hq: work that spans several sessions or departments gets its own folder (`initiatives/<slug>/`, with a one-page `status.md`), every folder of documents gets a one-line `README.md` index that agents read first, and the weekly brief gains a hygiene step that reports files over budget, old documents, long-open pending items, idle initiatives, contradictions, stale claims, orphans and missing links, and proposes what to archive for the CEO to approve. v0.13.0 archives a removed department's folder instead of deleting it: its documents move to `archive/departments/<id>/` with the same archiving steps, and the folder is deleted only when the CEO asks for that explicitly. <!-- x-release-please-version -->

## 1. Problem

One person, many organizations. A solo founder may run a product company, a second venture, and their own affairs as an entrepreneur (accounting, tax, personal legal, portfolio, personal brand). Context for each lives in separate places, shared context has no structure, and the CEO checks many queues to learn what needs them.

AI agents help, but unstructured they have predictable failures: decisions are made in chat and forgotten, numbers are invented, outward-facing actions happen without approval, and work and personal accounts get mixed. The framework gives each organization a written, auditable structure and gives the CEO one place to look.

The pattern was proven in one running instance (the reference instance, the author's first product org). This spec generalizes it.

## 2. Goals and non-goals

**Goals**
- One entry point per org: a chief of staff (CoS) the CEO talks to.
- Departments as vertical specialists with charters and explicit tool allowlists.
- A git repo per org as the single source of truth.
- One aggregated list of what waits on the CEO, across all orgs.
- Cheap by design: the top-tier model plans, cheaper models execute.
- Safe by default: a configurable approval-gate table.

**Non-goals**
- No hosted service. Everything runs locally in Claude Code against files the CEO owns.
- No scheduled automation by default. Rhythms (weekly brief, reviews) run on demand.
- Agents never take outward-facing or irreversible actions without passing the gate.
- Finance, tax and legal departments are advisory. They never file, sign or submit anything and are not a substitute for professionals.
- Not a project-management tool. Issues and the roadmap stay in GitHub (the repos and Project registered in `org.yaml`); hq links to them, and the agents keep them current as they work.

## 3. Core concepts

| Term | Meaning |
|---|---|
| Framework | The versioned, reusable part: templates, catalog, skills, schemas, wizard |
| Instance | One org's hq repo, generated from the framework and owned by the CEO |
| Level | `holding` (the CEO as entrepreneur) or `company` (one per product, with its own code org and hq repo) |
| Purpose | What the fleet is for: job (the CEO's own work at an employer), product, startup, company or personal (the CEO's own personal life). Set by the first wizard question; drives suggested departments, account rules and holding eligibility (see 6) |
| Chief of staff (CoS) | The CEO's single point of contact per org. Frames, routes, records, challenges. Owns hq. Does no deep execution |
| Department | A vertical specialist agent with a charter, a tool allowlist and a model tier |
| Charter | A short file stating a department's scope, what it never does, its inputs and outputs, and its gates |
| Handoff | A note a department leaves in `inbox/` for the CoS at the end of its work |
| Decision card | A pending question: context, options, recommendation, and who proposes it (or "needs analysis by <department>") |
| Decision record | A numbered, immutable file in `decisions/` recording an answered card |
| Approval gate | A rule saying which actions are free, need notice, or need the CEO's explicit OK |
| CEO pending list | The one list of what waits on the CEO: actions (`A`) and decisions (`D`), with codes and a kind (`{ok}` approve, `{do}` the CEO does it, `{decide}` a card) that a script or a front-end can read. Lives in `company/state.md` under "Waiting on the CEO". Tasks the CEO owns personally (`T` codes) live apart, in the optional `company/todo.md`. Items can have one level of child items (indented, each with its own code and kind); a parent whose own ask is answered shows `{wait}` until its children are done. |

## 4. Framework vs instance

The framework is a versioned Claude Code plugin. An instance is an hq repo per org. Framework upgrades never overwrite instance files. An upgrade ships as a migration: an explicit, reviewable diff the CEO (via the CoS) applies as a normal commit. Instance files record the framework version they were generated from.

**Plugin layout**

```
ceo-of-agents/
  .claude-plugin/    plugin.json, marketplace.json
  templates/
    instance/        CoS CLAUDE.md template and all hq files, with placeholders
    department/      custom department: charter + agent; the document index of every department
    workers/         reader and worker agent templates, one pair per instance
    policies-repo/   policy.yaml and README.md for the holding's separate policies repo
  catalog/           department catalog (charter + agent template each)
  skills/            init-fleet; CoS procedures: session-start, intake, record-decision, weekly-brief, hq-version, departments, product-repos, initiatives, draft-as-ceo, portfolio-brief
  schemas/           state.md, org.yaml, portfolio.yaml, policy.yaml, handoff, decision card, decision record, document lifecycle, initiative, boot set, CEO todo list, CEO voice, tips file
  tips/              tips.yaml: contextual tips (a text and a phrase to say)
  gates/             default approval-gate table
  migrations/        vN-to-vN+1 diffs
```

There is no `agents/` dir: Claude Code auto-registers every `.md` under a plugin's `agents/` as a live subagent, so templates with placeholders cannot live there.

**Instance (hq) layout**

```
<org>-hq/
  CLAUDE.md                     CoS instructions (generated)
  org.yaml                      level, purpose, id, CoS name, language, models, gates, policy pin (company) or policies_repo (holding)
  operating-model.md            how the CEO works with this org
  company/
    state.md                    living snapshot, fixed schema (see 5)
    decision-queue.md           open decision cards
    todo.md                     optional: tasks the CEO owns (T codes), not in the boot set
    ceo-voice.md                optional: the CEO's voice for drafts under their name, not in the boot set
    briefs/                     dated briefs
  decisions/README.md           index of decision records
  decisions/NNNN-<slug>.md      numbered decision records
  inbox/                        handoffs, deleted once processed
  departments/<dept>/charter.md
  departments/<dept>/README.md  one-line index of the department's documents
  initiatives/README.md         index of initiatives (work across sessions or departments)
  initiatives/<slug>/           status.md (one page), README.md index, documents
  metrics/README.md             metric definitions, sources, dates
  archive/                      documents no longer current, same paths; skipped by default searches (.ignore)
  .claude/agents/<dept>.md      department agents with tool allowlists
  .claude/agents/reader.md      read-only worker (bulk reading, research)
  .claude/agents/worker.md      hands-on worker (file writes and commands)
  portfolio.yaml                holding only
```

**Keeping the hq lean.** An hq grows every day, but most of it is read on demand and costs nothing until needed. What every session pays for is the boot set: the files the CoS reads at session start (`CLAUDE.md`, `org.yaml`, `company/vision.md`, `strategy.md`, `state.md`, `decision-queue.md`, `accounts.local.yaml`). These rules keep it small and easy to search:

- `CLAUDE.md` holds identity, gates, house rules and a map. Procedures needed only sometimes are hidden plugin skills loaded on demand: `session-start` (the start-of-session routine), `departments` (adding, changing or granting access to a department), `product-repos` (registry, planned repos, clone paths, `gh`), `close-org` (closing a finished org, read-only from then on, and reopening it, each through a decision record; nothing is deleted), `draft-as-ceo` (drafts under the CEO's name, in their voice), next to `intake`, `record-decision`, `weekly-brief` and `hq-version`. Departments cannot load skills, so every rule a department needs stays in `CLAUDE.md` or in its own files. The CEO voice follows the same rule: what a department needs is in the hq file `company/ceo-voice.md` (its first section explains how to use it), not in the skill, which is the CoS's fuller procedure.
- **The CEO's voice.** Two levels are kept apart. How agents talk to the CEO in chat is `ceo.profile` in `org.yaml`. How text sounds when it goes out under the CEO's name (messages, mails, Slack, posts, slides, and GitHub pull requests, issues and comments made from the CEO's account) is the voice, an optional file `company/ceo-voice.md`, or the path that `ceo.voice` in `org.yaml` names (`schemas/ceo-voice.md`, `voice/1`). A draft comes in one fenced block (mail: `Subject:` line, blank line, body) so a front end can copy it. It is never used in chat with the CEO or in hq files. There is one voice per hq and nothing is inherited from a holding; only the CEO changes what it says, and agents propose lines. The file holds Base, then channel deltas with dated examples, then audience deltas; a draft composes them in that order and the later layer wins, so there are no entries per combination. It is opt-in and not in the boot set, created on first use. Because departments cannot load skills, its first section, "How to use this file", carries the rules, and the departments' agent files and the `CLAUDE.md` section for department agents point to it; the hidden `draft-as-ceo` skill is the CoS's fuller procedure and stays consistent with it. A draft is never sent or posted by the voice: sending stays behind the gates `contact-people` and `publish`. Raw samples of anyone's messages are never stored, only derived rules. A correction from the CEO ("too formal") becomes one proposed line, added only on a yes. The voice is set up intent first: the CEO says how they want to sound outward (overall, then per channel and audience); samples from sources the CEO names (sent messages, attached files or the conversation, none assumed) only calibrate it; where they disagree the stated intent wins and the gap is shown in one line; and a draft of the file is shown before anything is written. An empty or missing voice never blocks a draft: the channel mechanics apply alone.
- A budget per boot file and for the whole set (`schemas/boot-set.md`). Budgets are stated in bytes. The plugin ships `scripts/check-boot-set.sh`, which measures the set and also checks the pending lines; the `session-start` skill and the weekly brief report its output (one status line naming the offending files and lines) instead of doing the arithmetic themselves.
- Summaries are rewritten, history is logged. A line of `state.md` and the State and Next step of an initiative's `status.md` say what is true now and are rewritten when it changes; what they said before goes, verbatim and dated, to an append-only log outside the boot set (`company/log.md`, `initiatives/<slug>/log.md`; `schemas/log.md`). Initiative pages get a budget of their own, and every skill that writes `state.md` or a `status.md` measures the lines and the file it touched before its commit (with Grep and `wc -c`, which need no prompt) and fixes them, so a summary does not turn into a work log between two session starts.
- Analyses and notes carry lifecycle frontmatter (`status`, `as_of`, `source_commit`, `superseded_by`; `schemas/document.md`). Archived documents move to `archive/`, which `.ignore` keeps out of default searches while git still tracks it.
- Work that spans several sessions or departments gets one folder, `initiatives/<slug>/` (`schemas/initiative.md`): a one-page `status.md` (goal, state, next step, links) that only the CoS edits, and the documents the departments write for it. An open initiative costs one line in `state.md`; on close it gets a short summary and, with the CEO's OK, moves to `archive/`. Work that one department finishes in one go stays in `departments/<id>/`. The hidden `initiatives` skill holds the steps.
- Every folder of documents has a `README.md` index, one line per document, kept by whoever writes there. Agents read the index first and open only the document they need. Indexes and initiative pages are read on demand, never at session start.
- The weekly brief runs a hygiene step: files over budget, current documents whose `as_of` is more than 90 days old, pending items open for more than 14 days, idle initiatives, and four lint checks (contradictions, stale claims, orphans, missing cross-references). It proposes an archive list; nothing is archived without the CEO's OK, even though archiving removes nothing from git.

A holding instance is an org like any other whose specific job is to be a registry: `portfolio.yaml` lists references to company hqs, which may live in separate code orgs. It does not keep its policies in the hq: they live in a separate small policies repo (see 5), whose path is recorded in `org.yaml` as `policies_repo`. Its departments are chosen at setup like in any org, and may be none.

## 5. Cross-org context

This is the core value. The mechanism is deliberately simple: files, git, read-only reads. Nothing is copied, synced or automated.

### Upward: company to holding

Each instance exposes `company/state.md` as its standard interface, with a fixed schema.

```yaml
---
schema: state/1
org_id: ACME
level: company
last_updated: 2026-01-15
framework_version: 0.23.0  # x-release-please-version
next_action: 1
next_decision: 1
---
```

Fixed sections, in order: Products and status; Key numbers (each with source and date); Risks; Open decisions; Waiting on the CEO. Line formats live in `schemas/state.md`.

Codes are written namespaced in every file (`ACME-D12`, `ACME-A3`), are monotonic per org and never reused; `next_action` and `next_decision` hold the next numbers. Every decision card carries its own D code.

The holding keeps `portfolio.yaml`:

```yaml
schema: portfolio/1
stale_after_days: 14
orgs:
  - id: ACME
    name: Acme
    path: ~/work/acme-hq        # local clone
    remote: <git remote>        # the hq remote
```

The holding CoS never pulls. For each registered hq it runs `git -C <path> fetch`, then `git -C <path> show origin/<default-branch>:company/state.md`, so the clone's working tree is never touched. The Organizations line records when a clone is dirty, on another branch or not fetched (the last fetched copy is then read, and marked). It never writes to a company hq. Staleness is visible from `last_updated` against `stale_after_days`. Reads use the CEO's own git credentials (the CEO is a member of every org); the holding stores no credentials and nothing is shared between orgs.

At session start the holding CoS also lists the pending items of its registered companies (read-only); the full analysis stays in the portfolio brief.

A job or personal hq (`org.purpose: job` or `personal`) is never registered; the portfolio brief skips one if listed, reading only `org.purpose` from its `org.yaml`.

### Downward: holding to company

Policy layering: framework defaults < holding policies < company overrides. A company may tighten a holding policy, never loosen it. A job or personal hq never pins a policy.

| Policy area | "Tighten" means | Example |
|---|---|---|
| Approval gates | Move an action to a stricter tier | "Merge" from notice to explicit OK |
| Account separation | Add a restriction | Forbid a connector the holding allows |
| Language | Add a requirement | Files must be in a stated language |
| Models | Lower a ceiling | Cap workers to the cheapest tier |

The holding keeps its policy in a separate small policies repo, not in its hq. The repo has only `policy.yaml` (schema `policy/1`: minimum gate tiers, forbidden connectors, required file language, model ceilings for the CoS, departments and workers) and `README.md` at its root, and no sensitive data, because it is shared with every company's CEO clone. The holding `org.yaml` records it as `policies_repo` (`local` path, `remote` or `""`). Changing a policy is a commit in that repo approved by the CEO (`change-policy-rules`, tier ok). A company hq pins a commit of it in `org.yaml`:

```yaml
policy:
  repo: <policies repo remote>
  local: <path>                 # CEO's local clone of the policies repo, read-only
  pin: <commit sha>
```

At session start the company CoS runs an optional `git -C <local> fetch` (it may fail offline), then `git -C <local> show <pin>:policy.yaml`, and compares four areas: gates (company tier at least as strict as the holding minimum), connectors (no holding-forbidden connector granted to any department), language (file language matches the required one), models (`models.cos` not above `models.ceiling.cos`, no company department above `models.ceiling.departments`, no worker above `models.ceiling.workers`). It reports `Policy check: OK` or one line per loosening, and adds an `A` item. It never fixes silently. If the policy is unreadable it says "skipped: <reason>". Moving the pin is an explicit commit the CEO approves. The company never needs a clone of the holding hq.

### Aggregated CEO pending list

Codes are namespaced per org: `ACME-D12` (decision), `ACME-A3` (action). The holding CoS composes one list across all orgs in its brief, ordered by urgency and level. Items are resolved in the owning org: the CEO answers there, and the owning CoS records it. The holding list is a view, never a second source.

### Escalation

When a company decision touches money, personal liability or the portfolio, the company CoS marks the card `escalate: holding`. The holding sees it on its next read of `state.md`, adds context (tax, personal legal, cash across orgs) and puts its advice in the holding brief next to the namespaced code. The CEO carries it into the owning org when answering the card. The holding never writes to a company hq, so the decision is still recorded only where it belongs.

## 6. Setup wizard

`/ceo-of-agents:init-fleet` runs in an empty directory, where the plugin is installed at project scope (that install writes only `.claude/settings.json`), and asks:

1. Purpose and level: what the fleet is for (job, product, startup, company, personal); level (holding or company) is asked only for company, and job, product, startup and personal are company-level hqs.
2. Org name and short id (used in codes).
3. What the org is about: what it does and for whom, why it exists, and its stage (for a job: role and team, what good work looks like; for a holding: personal goals and portfolio direction; for personal: the part of life the fleet looks after and what would make it worth it, stage setting up or running). The answers become `company/vision.md` and `company/strategy.md`, which the CoS reads at session start.
4. Language for files. (The chat language is asked first, before question 1, or inferred from text typed with the command.) Free-text answers can be multi-line lists and are kept verbatim.
5. Departments: nothing is preselected, with relevance notes from question 3. One question covers four ways to build the org: take catalog entries as they are (the plain path, with no further question), take an entry and change it (scope, exclusions and tools; everything else stays from the catalog), define custom ones, or bring the CEO's own agents or skills, registered as they are (charter, routing row, gates and account rules; their files are never edited, and they can replace a generated department or be the only ones). An overlap check then warns, never blocks, when two departments cover the same work; it runs again when a department is added later with the `departments` skill. None is valid. The advisory entries health, money and paperwork are listed only for a personal hq. For every custom department the wizard asks scope, triggers, exclusions and the single core job, so no placeholder is left in its files. Every non-advisory department gets a limited `Bash` and no Edit or Write, so the wizard does not ask about commands.
6. Names or personas per agent, including the chief of staff's name (the role name or a persona, the CEO's choice; the CoS name is required).
7. Approval gates, in plain words with one example per action (ids stay in `org.yaml`): accept, make something stricter, or make something looser after a warning.
8. Model tiers for the CoS, departments and workers, with a per-department option "top model, workers included" (`workers: same`).
9. For a company with purpose product, startup or company: the holding's policies repo (remote), the local clone and the pin (optional). If a policy is given, the tighten-only check runs before anything is generated. For a job hq: an optional pointer to the employer's rules on data, AI tools and accounts. A holding and a personal hq skip this question.
10. Repositories and attribution: how commits and pull requests are signed, written to `attribution` in the hq's `.claude/settings.json` (absent: Claude Code default; custom text; or empty strings for none). A product repo or the issues home can be recorded as not yet existing (`planned: true`); the setup then seeds an action item asking the CEO to create it. Each repo other than the hq gets one plain question that sets `protected`, and when such a repo is given the wizard says, in one line, to clone it next to the hq folder, never inside it. Product repos and the roadmap board are not asked for a holding or a personal hq. Any optional question can be answered "later": it becomes an action item in the pending list.

After question 1 the wizard offers, once and opt-in, to read the services already connected in the session to pre-fill names, channels and repos. Declining (or not answering) changes nothing. Otherwise the CEO marks, per service, which belong to this org; only those are read, read-only (list, search and read tools only), and only for names; every fact found is a proposal the CEO confirms before it lands in an answer or in a charter's inputs. Reading grants nothing, and the setup record names the services read.

The wizard asks nothing about granting connectors. Every department starts with none (least privilege) and gets one later only through a decision card with a one-line reason; advisory departments (legal, finance, tax, health, money, paperwork) get read-only connector tools only, named one by one (no server wildcard). The CoS asks nothing about connectors either: the written rule in `CLAUDE.md` forbids using another account's connectors for the org. `accounts.forbidden_connectors` in `org.yaml` starts empty; an entry is added later only through a decision.

The wizard also offers an optional remote for the hq, added with `git remote add` and never pushed. Without a remote, the CoS skips pull and push and says once "No remote: pull and push skipped". A holding additionally creates its policies repo at a path the CEO gives (outside the hq; the only write outside the current directory): `git init`, renders `policy.yaml` and `README.md` from `templates/policies-repo/`, asks before its first commit, and offers an optional remote the same way. For a job hq the wizard also asks where the remote lives (a personal or an employer account) without imposing one, and reminds the CEO of the employer's rules.

It generates `CLAUDE.md`, `org.yaml`, `operating-model.md`, the `company/` files with empty schema-valid state, one charter and one agent file per department (agent files are named after the department's persona in lowercase, or its id when it has none; charters are named after the id), a `README.md` document index per department, `initiatives/README.md`, `decisions/README.md`, `inbox/README.md`, `metrics/README.md` and an initial decision record (`0001`) capturing the setup answers. It also generates `.claude/agents/reader.md` and `.claude/agents/worker.md`, and merges into `.claude/settings.json` Claude Code permission rules derived from the gates (section 7), including `Skill(ceo-of-agents:*)`, so the plugin's own skills run without a prompt, also in non-interactive runs (`claude -p`), once the folder is trusted (Claude Code applies a project's allow rules only after its workspace trust prompt is accepted). Before the first commit it checks that the plugin is installed for this folder (a project-scope install is tied to one path) and offers to install it, or prints the command. A holding also gets `portfolio.yaml` and the separate policies repo. It keeps the `.claude/settings.json` that the project-scope install wrote, so a new clone or a new computer finds the plugin enabled; if that file is missing, it writes it only with the CEO's OK. It never pushes and asks before the first commit.

**Fleet purpose**

| Purpose | Level | Account rule | Holding |
|---|---|---|---|
| job | company (not asked) | The employer's accounts and connectors used for this job are this org's accounts; the CEO's personal accounts and other orgs' accounts are kept out | Never registered, never pins a policy; an optional `employer_rules` pointer instead |
| product | company (not asked) | Employer accounts kept out | May be registered, may pin a policy |
| startup | company (not asked) | Employer accounts kept out | May be registered, may pin a policy |
| company | asked: company or holding | Employer accounts kept out | Company: may be registered, may pin a policy. Holding: is the registry |
| personal | company (not asked) | The CEO's own accounts; employer accounts kept out. Personal data lives only in `private/`, a git-ignored folder of the hq that stays on the computer; tracked files hold structure, decisions and pointers. No product repos or roadmap | Never registered, never pins a policy, no employer rules |

Suggested departments per purpose are in `catalog/README.md`, section "Suggestions by purpose". They are suggestions only; nothing is preselected. Design and brand is suggested for product, startup and company (company level), for visual and brand work only. The org chart needs no department: at the first session the CoS offers to draw it from `org.yaml` and does so only on the CEO's yes; a design and brand department, if there is one, can then make a polished version for sharing. For a job hq the chart is for the CEO, not a deliverable for the employer. A holding gets no suggestions, and a personal hq keeps its advisory-only suggestions.

**Starting department catalog**

Catalog entries are templates, not defaults: each org decides its own structure. Picking the same entry in two orgs creates two independent departments with separate charters and memory.

| Department | Purpose | Default tool allowlist idea | Default gate notes |
|---|---|---|---|
| Engineering | Code, CI, releases, security | Read, shell (limited), may spawn `reader` and `worker` (writes through `worker`); repo access for the org only | Open PRs free; merge, deploy, secret rotation need OK |
| Design and brand | Identity, assets, tone of voice, brand review | Read, shell (limited), design-tool connector, may spawn `reader` and `worker` (writes through `worker`) | Brand-rule changes need OK; publishing needs OK |
| Business | Model, pricing, market, competitors, discovery | Read, shell (limited), web search and fetch, may spawn `reader` and `worker` (writes through `worker`) | Contacting people or spending needs OK |
| Growth and social | Editorial calendar, post drafts | Read, shell (limited), web search, may spawn `reader` and `worker` (writes through `worker`) | Drafts only; publishing needs OK |
| Legal | Privacy, terms, policies, accuracy of claims. Advisory | Read, edit, web search; read-only connectors; no Agent tool | Never signs or files; routes to a professional on request |
| Finance and accounting | Bookkeeping views, cash, invoices review. Advisory | Read, edit; read-only connectors; no payment tools; no Agent tool | No payments or transfers; spending needs OK |
| Tax | Tax position, deadlines, document checklists. Advisory | Read, edit, web search; read-only connectors; no filing tools; no Agent tool | Never files or signs; deadlines surface as `A` items |
| Operations | Admin, vendors, tooling, calendars of obligations | Read, shell (limited), scoped connectors, may spawn `reader` and `worker` (writes through `worker`) | Subscriptions and vendor contact need OK |
| Health (personal only) | Health records, appointments, visit preparation. Advisory | Read, edit, web search; read-only connectors; no Agent or Bash | Never diagnoses or contacts anyone; personal detail in `private/` |
| Money (personal only) | Personal budget, bills, savings, tax deadlines. Advisory | Read, edit, web search; read-only connectors; no payment tools; no Agent or Bash | Never pays, transfers or invests; personal detail in `private/` |
| Paperwork (personal only) | Documents, contracts, renewals, forms. Advisory | Read, edit, web search; read-only connectors; no filing tools; no Agent or Bash | Never files, signs or sends; personal detail in `private/` |

## 7. Approval gates

Default table (`gates/default.md`), configurable per org: `org.yaml` holds `gates: {free, notice, ok}` lists of stable action ids.

| Tier | Action ids |
|---|---|
| free | `issues-and-labels`, `comments`, `drafts`, `open-pr`, `research`, `hq-write` |
| notice | `push-non-deploy-branch`, `hq-commit`, `dispatch-pushing-department` |
| ok | `merge`, `deploy`, `publish`, `contact-people`, `spend-money`, `rotate-secrets`, `delete-data`, `org-or-repo-settings`, `change-brand-rules`, `change-policy-rules`, `file-or-sign`, `make-payment` |

Tier order: free < notice < ok.

| Tier | Rule | Examples |
|---|---|---|
| Free | Do it, mention it | Issues and labels, comments, drafts, opening PRs, research, writing in hq (CoS) |
| With notice | One line before acting (what, where, content) | Pushes to a non-deploying branch, hq commits, dispatching a department that will push |
| Explicit CEO OK | Narrow, exact request, batched | Merge, deploy, publish, contacting people, spending money, rotating secrets, deleting data, org or repo settings, changing brand or policy rules |

Protected repos (`org/5`). The table applies to the org's own repos. Each item in `repos:` declares `protected: true|false`. On a protected repo (other people work there) every write needs the CEO's explicit OK, whatever its tier: issues, comments, pull requests and branch pushes included; reads stay free. The hq is never protected; every other repo defaults to protected and is set once, at registration, with one plain question ("Do other people work on this project and see what your agents write there?"; "not sure" keeps it protected). Protection is declared, never inferred from the owner, because the plugin cannot tell whether an account or org is the CEO's own. An unregistered repo counts as protected. Advanced, on request only: an owner pattern (`owner/*`) with exact items as exceptions.

Permission rules (`gates/permissions.md`, since 0.15.0). The gates are rules the agents follow; Claude Code's own permission rules decide when it prompts. Without a bridge, a fresh hq prompted for nearly every command, read-only ones included, which is worst in non-interactive runs. Setup, a migration and every later change to `gates:`, `repos:`, `tracker:` or `accounts.forbidden_connectors` write rules into the hq's `.claude/settings.json`, merged, never replacing other keys or the CEO's own rules. Commands are sorted into rule groups (reads on GitHub and `gh api` reads, syncing the hq, the plugin's files, editing the hq, committing, pushing the current branch, issues, comments, pull requests, the tracker, merge, release, settings, secrets, deletes, `gh api` writes, the deny baseline); each group carries the actions it can perform, and its tier is the strictest of them in this org. Free and notice groups go to `allow` (since 0.16.0; notice means "say it in one line, then act", and the line is not an OK, so a prompt would be a second gate), except groups whose commands a rule cannot hold to their purpose (issues, comments, pull requests and Project items: a rule cannot hold them to one repo or to their text): those never go to `allow` and keep their prompt (since 0.15.1; an allow rule allows whatever its `*` stands for, so no allowed rule may have a `*` that can carry a shell, an interpreter, a file write, a git option that runs a program, or a GitHub write). Two guarded wildcards are the exception (since 0.16.0): `gh api *` for reads and `gh pr merge -R <slug> *` for repos that are not protected, each allowed only while its guards (an explicit method or a body option for `gh api`; `--admin`, a second repo in any spelling or a URL for the merge) are in `ask`. Pushes are split: the hq's own save, the current branch to its origin, has two exact allow rules (`git push origin HEAD`, `git push -u origin HEAD`; a bare `git push` or `git push origin` depends on `push.default` and `remote.origin.push` and could push more, or a `+` refspec, so it is not allowed) and every other form keeps Claude Code's prompt; a rule cannot see the branch or the repo, so a push from a checkout that deploys on push stays a gate matter, and an org with any registered `protected: true` repo gets the two push rules in `ask` instead (a push carries no repo name, so it cannot be told apart from a push to a protected repo; an unregistered repo does not trigger this). Ok groups go to `ask` (which wins over any allow rule, in any settings file, and prompts in every permission mode, auto included). Writes on a protected repo always go to `ask`; issue, comment and pull request rules name the repo (`-R <slug>` right after the subcommand). Forbidden connectors become `deny` rules. A deny baseline (since 0.16.0) is written in every org whatever its gates and refuses in every mode: force push, remote branch deletion, history rewrites, `git clean` with force, `gh repo delete`, `gh release delete` and `gh api` DELETE; the deny rules also cover a git option before `push` (`git -C x push --force`) and quoted-colon deletes; `git reset --hard` always asks instead, since it is the way out of a stuck rebase. Deny rules match the usual spellings, not every one: a backstop, not the gate. An org can choose `ask` for the baseline instead (`gates.destructive: ask`, asked once at setup): the commands then prompt in every mode, so a user who has approved one can run it from a front end that drives `claude -p`, at the cost that a prompt approved by mistake runs it. Read-only shell commands and reads inside the hq need no rule (Claude Code allows them already); web access keeps its prompt. Prefix rules cannot see the branch or the target of a command, so they reduce prompts and do not replace the gates: a prompt the CEO approves is not a gate's OK.

Principles: do not ask for OKs the table does not require; batch the asks into the pending list; run the exact approved action, nothing broader. Advisory departments (legal, finance, tax) never do `file-or-sign` or `make-payment` at all; no config can lower them. Changing a holding policy is `change-policy-rules` (tier `ok`): a CEO-approved commit in the policies repo.

## 8. Models and cost

| Role | Tier | Notes |
|---|---|---|
| CoS | Top | Plans, decides, judges, talks to the CEO |
| Department | Chosen per org (from the tier list) | Vertical specialist; orchestrates its own workers |
| Workers | One tier down from their parent (the lowest tier stays itself) | Bulk reading, drafting, code, commands |

Every instance ships two worker agents in `.claude/agents/`, generated from `templates/workers/`. `reader` has Read, Grep, Glob, WebSearch and WebFetch only: read-only research and bulk reading, returning conclusions, not dumps. `worker` adds Edit, Write and Bash: it makes every file change for the CoS and the non-advisory departments, which have no Edit or Write of their own. Neither has the Agent tool or any connector, and neither spawns agents or escalates. Both run on `{{MODEL_WORKERS}}`, one tier below `models.departments`.

Agent names and department ids. A department has two names. Its id (`departments[].id`, a role id such as `engineering`) is the stable key for `departments/<id>/charter.md`, decision cards (`proposed_by`) and handoff file names. Its agent name (`departments[].agent`, new in `org/4`) is the `name` of `.claude/agents/<agent>.md`: the persona in lowercase (for example `mike`), or the id when the display name is the role name. The wizard derives it and asks only when a name clashes with another department, `reader` or `worker`, or has no usable Latin letters. The CoS routes and dispatches by agent name, `Agent(...)` allowlists hold agent names, and the CEO opens a department directly with `claude --agent <agent>`.

Version check. At session start the CoS uses the hidden `hq-version` skill to compare `framework_version` in the hq with the installed plugin version. If the hq is behind, it lists the migrations in order and adds one A item asking the CEO's OK. It applies them only after that OK, one version step at a time, with a short summary and one commit per step. There are no hooks and no background process: the check runs when a session runs. The same check reads `claude plugin list --json` and, only when the plugin is installed in more than one scope that applies to this hq folder, adds one status line with the scopes, the versions, the version loaded and the command to remove each extra copy; it is silent otherwise. Migrations stay documents in the plugin's `migrations/` folder.

Who may spawn what: every non-advisory department `Agent(reader, worker)`; advisory departments (legal, finance, tax, health, money, paperwork) no Agent tool at all. When an advisory department needs bulk reading, the CoS dispatches a `reader` for it. Known limit: the `Agent(type)` allowlist is enforced only when the department runs as the main thread of `claude --agent`. When the CoS dispatches a department as a subagent, any type list is ignored, so the rule there is that departments spawn only `reader` and `worker`, and advisory departments carry no Agent tool so nothing can be spawned from them.

Rules: workers never escalate to a more capable model than their parent. Departments delegate to workers and do not hand work back up. The CoS and the non-advisory departments make every file change through a worker; the CoS keeps hq commit and push, issue and pull request writes, merges and spot reads. Bash, for the CoS and every department, is only for git, gh, running tests or builds and single spot checks: never to write files and never to read many files (bulk reading goes to `reader`, writes go to `worker`). Every result is verified (diff read, check run) before it is built on or reported. Briefs to workers are self-contained: goal, files, constraints, definition of done, what to return.

## 9. Separation and privacy

- Each department has an explicit `tools:` allowlist; connectors are granted per department, not globally.
- Never mix accounts: credentials and connectors for org A are not used for org B. Use only this org's accounts: in a job hq (`org.purpose: job`) the employer's accounts used for that job are this org's accounts and the CEO's personal accounts are kept out; in every other org other accounts (for example an employer's) are never used.
- Advisory departments (legal, finance, tax, health, money, paperwork) get read-only connector tools only, named one by one.
- A personal hq keeps personal data only in `private/`, which its `.gitignore` excludes: it never reaches git or a remote and does not travel between computers (the CoS says so when it is empty on a computer). Secrets stay out of hq, `private/` included.
- The holding holds the most sensitive data (tax, personal legal, finances). Its repo stays private.
- Upward, cross-org reads happen only through the holding CoS, read-only, through `state.md`. Sensitive detail stays out of `state.md`.
- Downward, the only cross-org read is the company CoS reading `policy.yaml` from the pinned commit of the holding's separate policies repo. Departments never read it. A company never needs a clone of the holding hq, which stays private. The policies repo holds no sensitive data and is shared with every company's CEO clone.
- Numbers always carry source and date. If unknown, say so. Never invent a metric.

## 10. Roadmap

| Phase | Scope |
|---|---|
| 0 | Extract the framework from the reference instance, with no behavior change there |
| 1 | Build a holding instance from the wizard |
| 2 | Link the holding and the reference instance, read-only |
| 3 | Publish the framework |

Migrating the reference instance onto the framework happens only after v0 exists. v0.1.1 applied the review fixes to phase 0 (see the status line at the top).

## 11. Open questions

1. `state.md` schema versioning: `schema: state/1` exists; the announcement and compatibility policy (how breaking changes are announced, how long older versions are read) is still open (see `migrations/README.md`).
2. More than one human per org (a partner, a read-only professional): out of scope for v0. To keep the door open, "CEO" is a role with an id in `org.yaml`, not a hard-coded person.
3. License: resolved, MIT.
4. Migration UX: how much of an upgrade can be applied automatically while still arriving as a reviewable diff?
5. Policy enforcement: v0: the CoS reads files at session start; a validator script stays open.
6. Pending-list staleness: v0: `stale_after_days` in `portfolio.yaml` (default 14) flags stale orgs; open: what to do beyond flagging.
7. Holding policy repo separation: resolved in v0.1.1. The holding keeps policies in a separate small repo with no sensitive data; companies pin a commit of it and need no clone of the holding hq.
8. Whether `allowed-tools` patterns for `git -C` in skills behave as intended (unverified).
