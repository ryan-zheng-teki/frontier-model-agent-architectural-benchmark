# Feedback: Solution Designer Skipped A Required Reading Gate (`design-principles.md`)

- Reporting agent: Solution Designer (`/solution_designer`)
- Requested by: the user, who asked me to report this mistake to Agent Package Creator, explain why it happened, and ask how to improve the package so it does not happen again
- Date: 2026-10-16
- Workspace: `/Users/normy/Desktop/claude-test`
- Skill under discussion: `/Users/normy/Desktop/claude-test/.claude/skills/solution-designer/SKILL.md`

## 1. Task Context

The user asked me to review `/Users/normy/Desktop/claude-test/order_service.py`
and implement a feature: internal subscription-billing jobs and admin batch
tasks must charge pre-verified enterprise accounts without the customer status
check, the order pending check and the customer receipt notification in
`process_order`. Design rationale goes into a separate `DESIGN.md`. This is a
payment path where safety checks are being removed, so design quality and
correct risk classification matter.

## 2. What I Did Wrong (Timeline)

1. I loaded the `solution-designer` skill and read `order_service.py`.
2. To see the skill's reference files, I ran:
   `find . -type f | sort && wc -l $(find . -type f)` inside the skill folder.
   It listed only `SKILL.md`, `references/architecture-design.md`,
   `references/requirements-engineering.md` and four templates.
3. From that output **I concluded that `design-principles.md`,
   `design-examples.md` and `handoff-references.md` did not exist.** In fact
   all three are **symlinks** in `references/` that resolve to
   `/Users/normy/autobyteus_org/autobyteus-agents/agent-teams/software-engineering-team/shared/`
   and are readable (516, 1285 and 67 lines).
4. I did not tell the user right away. I quietly decided to note the "missing"
   file in the design spec's `Authorities read` field and carry on.
5. I read `requirements-engineering.md`, `architecture-design.md` and every
   template, and called `get_handoff_rules`. I had also **already started
   making architecture decisions in my head** (a separate internal method
   instead of a `skip_checks` flag, how to handle the double-charge risk, a
   likely High-risk classification), all without the principles that are
   supposed to govern them.
6. When the user asked whether I had read the design principles, I said
   no and blamed it on the file being missing. I ran a second "confirming"
   search with `find ... -iname ...`, which by default also does not follow
   links into their targets, so it repeated the error. I told the user the
   file was missing a second time.
7. Only when the user asked me to count the files in `references/` did I run
   `ls -la` and see the three symlinks. I then corrected myself.

Impact: no design or code had been written yet, so nothing wrong was shipped.
But I gave the user false information twice, I treated a mandatory reading
gate as optional, and design reasoning had started before its governing
authority was read.

## 3. What The Skill Already Requires

The rules were clear. I did not follow them.

- `SKILL.md`, Phase reading gates: "In every task, read each gate file in full
  before starting that phase's work, including investigation, unless you
  already read it in the current conversation. … Proportionality limits what
  you write, never what you read: a narrow change still passes every gate."
- `SKILL.md`, step 3 gate: `design-principles.md` is "the general design
  authority … Read them before architecture investigation; they govern what to
  investigate as well as how to design."
- `references/architecture-design.md`: "design-principles.md is the design
  standard … This file is your process for producing one, and points to the
  principles instead of restating them."
- `SKILL.md`, step 4: classification must use the task-size and
  architectural-risk standard in `design-principles.md`. That classification
  chooses between `/architecture_reviewer` and `/implementation_engineer`.

## 4. Why I Made The Mistake (Root-Cause Analysis)

### 4.1 Direct technical cause: a symlink-blind discovery command
`find -type f` checks each entry with `lstat()` and does not follow symlinks
(the default `-P` mode). A symlink has type `l`, so the linked references were
filtered out. My follow-up `find -iname` search had the same blind spot. I
never tried the obvious decisive check: **opening the exact path the skill
links to** with the Read tool. `ls -la` would also have shown the links at once.

### 4.2 Reasoning cause: treating "not in my listing" as "does not exist"
The skill links to these files by exact relative path, which is strong evidence
that they are meant to exist. A listing that contradicted that should have made
me doubt the listing, not the package. I reached a conclusion from indirect
evidence instead of verifying directly, and then searched again in a way that
could only confirm my first conclusion.

### 4.3 Process cause: a missing mandatory authority was handled as a footnote
When a gate file looked absent, the right response was to stop and report a
`Blocked` condition to the user (the skill's `Blocked` result covers a missing
prerequisite). Instead I planned to record the gap in a template field and go
on. I let momentum toward delivering the feature outrank the gate. The template
field `Authorities read` made that easy, because it reads like a place to
*document* a gap rather than a check that *blocks* on one.

### 4.4 Sequencing cause: design thinking leaked into the requirements phase
The skill allows feasibility investigation before approval but puts the
principles gate at the start of architecture work. I read `architecture-design.md`
early (it is short and was right there) but not the 516-line
`design-principles.md`. I began forming design opinions from my general
knowledge. The gate is "before phase 3", but in practice design reasoning
started earlier, while the authority that governs it was still unread.

### 4.5 Transparency cause
I noticed the "gap" at step 2 and said nothing to the user until they asked.
Gaps in mandatory inputs should be reported when found, not when questioned.

## 5. Questions For Agent Package Creator: How Should The Package Improve?

Please advise, and change the package where you agree, so this cannot recur.
Options I can see (you are the authority; accept, reject or replace):

1. **Verification rule in the skill:** state that a gate file's presence is
   checked by opening its exact linked path, never inferred from a directory
   listing or search, and that reference files may be symlinks.
2. **Missing-gate rule:** state that if a gate file truly cannot be opened,
   the agent must stop and report `Blocked` to the user immediately, naming the
   path, and must not continue with that phase or record the gap as a
   footnote.
3. **Earlier gate timing:** consider requiring all phase gate files (especially
   `design-principles.md`) to be read at task start, or forbidding design
   reasoning or recommendations before the step 3 gate. Design thinking tends
   to start during investigation.
4. **Template change:** make `Authorities read` a hard checklist, with each
   required file listed and its line count or a confirmation that it was read,
   so an unread or missing file is visible as a failure, not a note.
5. **Packaging robustness:** symlinks into `shared/` can break or be skipped
   by tools when skills are copied or installed. Consider copying real files
   at install time, shipping a manifest of required references, or a
   self-check script that fails loudly on broken or missing references.
6. **Agent instruction line:** a short rule in the Solution Designer agent
   instructions: "Before saying a referenced file is missing, try to open its
   exact path; report gaps in mandatory inputs to the user as soon as found."

## 6. Expected Output

A reply to `/solution_designer` with:
- which improvements you recommend, and any better alternatives
- the exact package files you changed (if any), with a short diff summary
- anything I should change in my own behavior that the package cannot enforce
