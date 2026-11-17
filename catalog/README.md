# Department catalog

The catalog holds starting templates for departments. Each entry has two files:

- `charter.md`: scope, what the department never does, inputs, outputs, gates, handoff.
- `agent.md`: a Claude Code subagent template with an explicit `tools:` allowlist. Spawning is limited by type: the advisory entries (legal, finance, tax, health, money, paperwork) have no `Agent` tool and no `Bash`; engineering has `Agent(reader, worker)`; every other department has `Agent(reader)`. The type list is enforced in direct `claude --agent` sessions only. When the CoS dispatches a department as a subagent the list is ignored, so the department must still spawn only those types. The `reader` and `worker` agents come from `templates/workers/`.

| Id | Department | Advisory |
|---|---|---|
| `engineering` | Engineering | no |
| `design-brand` | Design and brand | no |
| `business` | Business | no |
| `growth-social` | Growth and social | no |
| `legal` | Legal | yes |
| `finance` | Finance and accounting | yes |
| `tax` | Tax | yes |
| `operations` | Operations | no |
| `health` | Health (personal only) | yes |
| `money` | Money (personal only) | yes |
| `paperwork` | Paperwork (personal only) | yes |

## How to read it

- Entries are templates, not defaults. Nothing is preselected; the setup wizard asks and zero departments is a valid answer.
- Picking the same entry in two orgs creates two independent departments, each with its own charter, agent file and memory. Nothing is shared between them.
- The wizard fills the placeholders (`{{DEPT_ID}}`, `{{AGENT_NAME}}` (the department's agent name; its agent file is named after it), `{{DISPLAY_NAME}}`, `{{ORG_NAME}}`, `{{ORG_ID}}`, `{{MODEL}}`, `{{WORKER_MODEL}}`, `{{WORKER_TIER}}` (how its workers relate to the department's tier: one tier down, or the same tier for a department set to top model, workers included), `{{OTHER_ACCOUNTS_EXAMPLE}}` (the account example, set by the org's purpose)). Every department starts with no connectors; the CoS adds one to the `tools:` list only after a decision card grants it.
- Once generated, the files belong to the org and can be edited freely. Gates in a generated hq live in `org.yaml`; advisory departments never file, sign or pay.
- Each agent file may name generic categories of optional external plugins. Nothing is vendored or installed by the framework; the CEO decides whether to add any.
- Four ways to build the org: take entries as they are; take an entry and change it (a "Changes for this org" section from `templates/department/changes.md` is appended to its charter and agent file, and its `tools:` line changes; everything else stays from the catalog); write a department from scratch (`templates/department/charter.md` and `agent.md`); or bring the CEO's own agents or skills, used as they are (only a charter from `templates/department/own-charter.md`). An overlap check warns, never blocks, when two departments cover the same work.
- `health`, `money` and `paperwork` are offered only in a personal hq (`org.purpose: personal`). They keep personal detail in the hq's git-ignored `private/` folder and put only pointers in tracked files and handoffs.

## Suggestions by purpose

Suggestions only. The wizard shows the line for the chosen purpose next to the list above; nothing is preselected and the CEO still picks each department or none. This table is the single source the wizard reads.

`design-brand` is suggested only for visual and brand work: identity, assets, voice rules and review of what the public sees. It is never suggested to draw the org chart: at the first session the chief of staff offers to draw that itself from `org.yaml`, with or without a design department; when one exists, it can turn the chart into a polished picture for sharing.

| Purpose and level | Suggested departments |
|---|---|
| `job` (company level) | `operations` (recurring obligations and work tools); `engineering` (only if the job is technical); custom departments that mirror the CEO's own work streams. Not suggested: `business`, `growth-social`, `legal`, `finance`, `tax` (they speak for the employer or cover the employer's own functions), `design-brand` (the employer owns its brand). |
| `product` (company level) | `engineering`, `design-brand` (visual identity and assets), `growth-social`, `business` |
| `startup` (company level) | `engineering`, `business`, `design-brand` (visual identity and assets), `growth-social`, `legal`, `finance` |
| `company` (company level) | `engineering`, `business`, `legal`, `finance`, `tax`, `operations`, `design-brand` (when the company has a brand or a public face to look after) |
| `company` (holding level) | None. Departments are optional for a holding; do not suggest any. |
| `personal` (company level) | `health`, `money`, `paperwork` (advisory: they prepare and remember, the professional decides); custom departments for other areas of the CEO's life. Not suggested: `legal`, `finance`, `tax` (they cover a company's functions; `money` and `paperwork` cover the personal side), `engineering`, `design-brand`, `business`, `growth-social`, `operations` (they work for an organization). |
