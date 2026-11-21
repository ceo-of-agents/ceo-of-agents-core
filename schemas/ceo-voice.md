# Schema: company/ceo-voice.md (`voice/1`)

An optional file that says how the CEO writes. It is used only for text that goes out under the CEO's name: messages, mails, Slack, posts, slides, and GitHub pull requests, issues and comments made from the CEO's account. It is never used in chat with the CEO (that is `ceo.profile` in `org.yaml`) and never in hq files.

The file is opt-in. An hq without `company/ceo-voice.md` behaves as before: nothing reads it, nothing creates it, and no check reports its absence. The optional key `ceo.voice` in `org.yaml` (`schemas/org.yaml`) can name it; when the key is absent or null, the file at `company/ceo-voice.md` is used if it exists. The chief of staff (CoS) creates the file from `templates/instance/company/ceo-voice.md` on first use, after the CEO agrees to a draft of it (`skills/draft-as-ceo/SKILL.md`, "Bootstrap"). The setup wizard does not copy it. One voice per hq: nothing is inherited from a holding.

Only the CEO changes what the voice says. The CoS and the departments propose a line; it is added only after the CEO says yes. It is not in the boot set (`schemas/boot-set.md`): the session start does not read it.

Departments cannot load skills, so the file explains itself: its first section, `## How to use this file`, holds the rules a department needs. The skill `draft-as-ceo` is the CoS's fuller procedure and must stay consistent with that block.

## Frontmatter (all fields required)

| Field | Type | Rule |
|---|---|---|
| `schema` | string | Exactly `voice/1` |
| `last_updated` | date | `YYYY-MM-DD`; updated whenever a line is added, changed or removed |

## Body

Optional H1 title line `# CEO voice` directly after the frontmatter. Then these H2 headings, in this order:

1. `## How to use this file`: a fixed block of about 12 to 18 short lines, copied from the template and not edited per hq.
2. `## Base`: what is always true of the CEO's writing.
3. `## Channels`: one `### <Channel>` subsection per channel (for example Slack, Mail, GitHub, Slides). Deltas only: what differs from Base. Each channel has one or two short examples that the CEO wrote or approved, each marked with its date: `Example (YYYY-MM-DD): "..."`.
4. `## Audiences`: one `### <Audience>` subsection per audience (for example Management, Customers). Deltas only.

An empty section or subsection is fine: it never blocks a draft.

## Rules

- **Composition.** Base, then the channel, then the audience. A later layer wins on a conflict. There are no entries per channel and audience pair.
- **Deltas only.** A channel or an audience says only what differs from the layers before it.
- **No raw samples.** The file holds rules and short generic examples, never a raw copy of a message the CEO or anyone else wrote. Raw samples never go into any file, log, commit, brief or handoff.
- **Examples are dated.** The date lets the weekly brief flag examples older than 180 days.
- **Captured corrections.** When the CEO corrects a draft, one line is proposed for the right section; it is added only after a yes, and `last_updated` is set.
- **Never sends.** The voice shapes a draft. Sending or posting stays behind the gates `contact-people` and `publish`.

## Minimal valid example

See `templates/instance/company/ceo-voice.md`: the How-to block and the four headings, with the three sections empty (each holds only a format comment). An empty section is valid. Sample rules, as below, belong only in this documentation, never in the template:

```markdown
## Base

- Conclusion first.

## Channels

### Slack

- No greeting.

Example (2026-01-15): "Build is green. Release at 16:00 unless someone objects."

## Audiences

### Management

- Decision asked and impact first.
```

## Draft format

A draft is delivered in one stable format, so a front end can copy it. The skill `draft-as-ceo` (step "Deliver") and the "How to use this file" block of the template both follow it.

- The draft goes in exactly one fenced code block with no info string, and nothing else is inside the block. If the draft contains a run of backticks, the fence is longer than the longest run (for example four backticks).
- Mail: the block's first line is `Subject: <subject>`, then one blank line, then the plain body.
- After the block, one short line says which channel and audience were applied. Any offer (set up the voice, add a channel section) comes after that line, outside the block.

## Validation checklist

- Frontmatter has the two fields; `schema` is `voice/1`.
- The four H2 headings exist, spelled exactly, in the stated order.
- Every example under a channel starts with `Example (YYYY-MM-DD):`.
- No raw message is stored: examples are short and generic.
- `ceo.voice` in `org.yaml` names this file, or is unset and the file is at `company/ceo-voice.md`; no script checks the file: the CoS keeps these rules.
