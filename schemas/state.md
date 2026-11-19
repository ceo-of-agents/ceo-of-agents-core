# Schema: company/state.md (`state/1`)

The living snapshot of one org. It is the standard interface a holding reads (read-only) to compose the CEO pending list. Owner: the chief of staff (CoS). Departments never edit it; they report changes in a handoff.

## Frontmatter (all fields required)

| Field | Type | Rule |
|---|---|---|
| `schema` | string | Exactly `state/1` |
| `org_id` | string | Same as `org.id` in org.yaml |
| `level` | string | `company` or `holding` |
| `last_updated` | date | `YYYY-MM-DD`; updated at the end of every meaningful session |
| `framework_version` | string | Framework version the file was generated from, e.g. `0.9.0` |
| `next_action` | integer | Next unused `A` number (starts at 1) |
| `next_decision` | integer | Next unused `D` number (starts at 1) |

## Body

Optional H1 title line `# State of the company` (or the org name) directly after the frontmatter. Then exactly these H2 headings, in this order, none missing, none added:

1. `## Products and status`
2. `## Key numbers`
3. `## Risks`
4. `## Open decisions`
5. `## Waiting on the CEO`

An empty section body is the single line `- none`.

## Line formats

Every line stays at most 300 characters, frontmatter included (budget: `schemas/boot-set.md`). An item that needs more keeps one line and links a note for the detail.

Rewrite, do not append: when a fact changes, the line is rewritten to the current fact. The history goes to `company/log.md` (`schemas/log.md`), and the line may end with `; history in company/log.md`. The skills check each line they touch before their commit (`schemas/boot-set.md`, "Check at write time").

Products and status:
`- <product>: <status in one line> (as of YYYY-MM-DD)`
`- <initiative title>: <state in a few words>, see initiatives/<slug>/status.md (as of YYYY-MM-DD)` (one line per open initiative; `schemas/initiative.md`)

Key numbers (never invent; unknown is allowed):
`- <metric>: <value> (source: <source>, as of YYYY-MM-DD)`
`- <metric>: unknown (no source yet)`

Risks:
`- <risk>: <impact>; owner: <cos|dept-id>`

Open decisions (one line per open card in decision-queue.md):
`- ACME-D3: <question> (since YYYY-MM-DD; proposed by <dept-id|cos>)`
`- ACME-D3: <question> (since YYYY-MM-DD; needs analysis by <dept-id>)`
The card in decision-queue.md carries the same fact as `- proposed_by: <dept-id|cos>` or `- needs analysis by: <dept-id>` (exactly one). Append ` [escalate: holding]` when the card has `escalate: holding` (company level only).

Waiting on the CEO (THE pending list: every open A item and every open D item):
`- ACME-A2 [high] {ok}: <what the CoS will do once the CEO approves> (since YYYY-MM-DD)`
`- ACME-A3 [normal] {ok}: start <issue or task>, <who would do it> (since YYYY-MM-DD)` (open work the CoS holds: not started, not routed; the OK starts it; work already running is not listed)
`- ACME-A4 [normal] {do}: <exact action the CEO performs: where, what, link> (since YYYY-MM-DD)`
`- ACME-D3 [normal] {decide}: decide <question>, see decision queue (since YYYY-MM-DD)`

The kind, in braces right after the urgency, tells a reader (or a script, or a front-end) what the item needs from the CEO:

| Kind | Code | Meaning | The CEO answers |
|---|---|---|---|
| `ok` | A | An approval: the CoS (or a department) carries out the action once the CEO says yes | "approve ACME-A2" |
| `do` | A | A task only the CEO can perform (a click in a console, a signature, a command on their computer, an answer only they have) | "ACME-A4 done" |
| `decide` | D | A decision card in `company/decision-queue.md` | "ACME-D3: option b" |
| `wait` | A or D | A parent whose own ask is answered, or that only groups its children: nothing on this line needs the CEO | nothing; the line goes with its last child |

Every line has exactly one kind. An A item is `ok` or `do`; a D item is `decide`; `wait` is only for a parent line, A or D, with at least one child (see "Parent and child items").

## Parent and child items

One piece of work often breaks down into several asks, and one decision can open follow-ups. A top-level item can have child items, one level deep, so the list shows what belongs together and what blocks what.

```markdown
- ACME-A7 [high] {ok}: launch the beta once the items below are done (since 2026-01-12)
  - ACME-A8 [normal] {ok}: approve the store copy in docs/beta-copy.md (since 2026-01-12)
  - ACME-D5 [normal] {decide}: decide the beta price, see decision queue (since 2026-01-13)
- ACME-D3 [normal] {wait}: pricing model decided (decision 0012); follow-ups below (since 2026-01-10)
  - ACME-A9 [low] {do}: update the price in the store console, Pricing > Edit (since 2026-01-15)
```

- A child line is indented by exactly two spaces and sits right under its parent or a sibling. It has the full line format (own code, urgency, kind, since date). No grandchildren: a child is never a parent.
- Any top-level A or D item can be a parent; children can be A or D items. A D parent is the usual way to group the follow-ups a decision opens.
- Every item is answered by its own code. Approving a parent never approves its children, and approving a child never approves its parent: gates stay per action.
- Children block their parent: the CoS carries out a parent's approved action only once all its children are done or dropped.
- Clearing a child removes only its line. When a parent's own ask is answered while children are still open, the parent line stays as the group's head: its kind becomes `{wait}` and its text says what was answered and when (for example `launch the beta: approved 2026-01-14, runs when the items below are done`). A decided D parent keeps its line the same way, with the decision record number, while it has open children; its card has left the decision queue and "Open decisions".
- A parent goes when its own ask is answered and its last child is gone: the CoS then carries out an approved parent action (citing the OK) and removes the line. A parent whose own ask is still open stays as an ordinary item once its children are gone.
- A new ask that belongs to an open item goes under it as a child. An existing item can move under a parent: it keeps its code and since date.
- Counting: a summary counts every line that asks something (kind `ok`, `do` or `decide`), children included; a `{wait}` line is a group, not an ask (for example "6 items, 2 groups"). When listing codes, each child comes after its parent: `ACME-A7 (ACME-A8, ACME-D5)`.
- `wait` is valid for an A or a D code, only on a top-level line that has at least one child.
- "Open decisions" stays flat (never indented).

## Codes

- `<ORG_ID>-A<n>` is an action for the CEO; `<ORG_ID>-D<n>` is a decision. Every decision card has its own D code.
- `<ORG_ID>-T<n>` is a task the CEO owns personally (reply to someone, chase an answer). T items live only in the optional `company/todo.md` (`schemas/todo.md`), with their own counter `next_todo` there; they never go in state.md, so "Waiting on the CEO" keeps only A and D items. A reader may show open T items next to them.
- Numbers are monotonic per org and never reused, even after an item is removed. The next numbers live in `next_action` and `next_decision`; increment them when a code is issued.
- Urgency is `high`, `normal` or `low`.
- Remove an item as soon as it is done; do not keep a "done" log (history lives in git and decision records).

## Privacy

Sensitive detail (tax, personal legal, personal finance) stays out of state.md. Refer to it by pointer only.

## Minimal valid example

```markdown
---
schema: state/1
org_id: ACME
level: company
last_updated: 2026-01-15
framework_version: 0.9.0
next_action: 5
next_decision: 4
---

# State of the company

## Products and status
- Acme app: private beta, 40 testers (as of 2026-01-14)

## Key numbers
- Weekly active testers: 31 (source: analytics dashboard, as of 2026-01-14)
- Monthly burn: unknown (no source yet)

## Risks
- Single maintainer for the release process: a release stalls if unavailable; owner: cos

## Open decisions
- ACME-D3: Adopt usage-based pricing for the beta? (since 2026-01-10; needs analysis by business) [escalate: holding]

## Waiting on the CEO
- ACME-A2 [high] {do}: Approve the store listing in the developer console, Listings > Draft > Approve (since 2026-01-13)
- ACME-A4 [normal] {ok}: approve merging the release pull request https://github.com/acme/app/pull/12 (since 2026-01-14)
- ACME-D3 [normal] {decide}: decide pricing model for the beta, see decision queue (since 2026-01-10)
```

## Validation checklist

- Frontmatter has all seven fields; `schema` is `state/1`; `org_id` and `level` match org.yaml.
- `last_updated` is a valid date and not in the future.
- The five H2 headings exist, spelled exactly, in the stated order, with no extra H2.
- No section is empty: use `- none`.
- Every code starts with `<org_id>-A` or `<org_id>-D` followed by an integer; no code is below the `next_*` counters' history (all issued numbers are less than `next_action` / `next_decision`).
- Every line in Waiting on the CEO has a kind: `{ok}` or `{do}` for an A code, `{decide}` for a D code, `{wait}` for a parent of either code (`scripts/check-boot-set.sh` in the plugin reports the lines that do not).
- Child lines are indented by exactly two spaces, follow a top-level item, never carry `{wait}` and have no children of their own; every `{wait}` line has at least one child (`scripts/check-boot-set.sh` in the plugin reports the lines that do not).
- No code appears twice within a section; no code is ever reused for a different item.
- Every open card in decision-queue.md has one line in Open decisions and one D line in Waiting on the CEO; every D line points to a card, except a `{wait}` D line, which names its decision record instead.
- "Open decisions" lines are never indented.
- Every Key numbers line has a source and date, or says `unknown (no source yet)`.
- Every dated item uses `YYYY-MM-DD`.
- No sensitive tax, personal legal or personal finance detail appears.
