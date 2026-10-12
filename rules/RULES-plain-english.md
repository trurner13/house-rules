# The rules, in plain English

All 58 rules from [RULES.md](RULES.md), written for a person rather than an agent.
Each says what the rule asks for and why it matters. The detail and the evidence
behind every rule are in the linked notes in `RULES.md`.

`RULES.md` is still the version that counts. It's the one copied into every repo and
read by the AI in every session. This file is the readable companion. Each entry ends
with the rule's name in `RULES.md`, and an automatic check fails if a rule is added,
renamed or removed there without being updated here.

## How we build

- **Humans design, AI writes the code.** In every repo, people decide what to build,
  how it fits together, and whether the result is right. The AI does all the actual
  code writing. *Why:* people stay in charge of the decisions that matter, and the
  work moves at the AI's speed. (In RULES.md: "AI-first repos, no human-written code")
- **Write the plan down before building.** Anything bigger than a small fix starts
  from a written description of what's wanted, which a person approves before the AI
  starts. The plan is updated as the work teaches you things; it is not finished and
  frozen before coding begins, and no particular planning tool is required. Work then
  happens in small steps that can each be checked. *Why:* the written plan, not the
  code, is what everyone agrees on. It's also what the result gets checked against.
  (In RULES.md: "Spec-first")
- **People steer at the start, not at the end.** Humans own the plan and the design.
  The AI then writes, reviews, tests and merges the change itself once every automatic
  check passes, with no one reading every line. Changes prompted by outsiders always
  wait for a person, and there's a one-step "hold" switch to stop anything. *Why:*
  reading every line doesn't scale. The catch is that the automatic checks carry all
  the safety, so they must be strong. (In RULES.md: "Human control is upstream, not at the merge")
- **Get the basics in place first.** Don't let AI loose on a repo until it has
  automatic testing, a reliable way to release, and agreed coding standards. *Why:* AI
  makes a weak process fail faster, not better. (In RULES.md: "Fundamentals first")
- **Every repo is set up the same way.** Claude's instructions, rules, skills, helper
  agents and settings sit in the same places in every repo. *Why:* the AI, and people,
  find what they need without learning each repo from scratch.
  (In RULES.md: "Standard repo structure")
- **Name things one way.** Repo names are lowercase with hyphens, like `acme-api`.
  Every repo has the same top-level folders, with nothing loose at the top: no stray
  PDFs, zip files or temporary folders. Branches are named after the issue they're for.
  Existing repos get renamed when they're next worked on. *Why:* any repo can be
  navigated at a glance, and clutter stops hiding what matters.
  (In RULES.md: "Name things one way")
- **A person must be able to use it without AI.** The README explains, in commands
  anyone can copy, how to set the project up, run it, test it and release it. Nothing
  essential is hidden in the AI's own files. *Why:* "AI writes the code" must never
  turn into "only AI can run it". That's a single point of failure, and it makes the
  repo impossible to hand over. (In RULES.md: "Usable by a human without Claude")
- **A fresh copy must just work.** Everything a new machine needs to build, run, test
  or understand the project is saved in the repo. Only secrets, files that can be
  regenerated, and truly machine-specific settings are left out. Anything the repo
  can't hold, like passwords or big datasets, is listed in the README with where it
  lives and who grants access. *Why:* handovers keep failing because one "ignored" file
  was actually essential. (In RULES.md: "A fresh clone is the deliverable")
- **Ask git what it's hiding; don't guess from the ignore list.** Whether a file is
  being left out depends on several settings, some of which exist only on one machine.
  So check with git's own command, then prove it by making a fresh copy and running
  the setup. *Why:* reading the ignore file gives the wrong answer in exactly the cases
  that break handovers. (In RULES.md: "Ask git what's ignored — never read `.gitignore`")
- **Never write a branch's name, or its working folder, into the code.** Scripts work
  out where the project is from where they sit, not from a folder named after the
  piece of work in progress. A test catches any that slip back in. *Why:* that folder
  disappears when the work is finished and merged, and every script that named it
  breaks — over a hundred of them did on one project. (In RULES.md: "Never hard-code a branch or a worktree")
- **Judge AI by work that actually ships.** Measure how many AI-made changes get
  accepted, how many needed no human fixing afterwards, and how many needed a fix within
  a week. Don't count lines, changes opened or logins. Money spent on AI is the cost side
  of that sum, not a sign of success or failure on its own. *Why:* the other numbers look
  impressive while telling you nothing. (In RULES.md: "Measure adoption by merge rate, not vanity metrics")

## How the AI talks to us

- **No flattery.** No "great idea" or "good catch". The AI leads with substance and
  says plainly when it disagrees or sees a risk. *Why:* praise hides weak points and
  makes the AI's judgement worthless. (In RULES.md: "No sycophancy")
- **Ask when unclear; don't guess.** If a request could mean several things, the AI
  lists them and asks, ideally as multiple choice with a recommendation. It only goes
  ahead without asking when the meaning is obvious. *Why:* a quick question is cheaper
  than building the wrong thing. (In RULES.md: "Clarify vague prompts — don't guess")
- **Plain English, always.** The AI explains what changed and why it matters, in
  everyday words. Technical terms appear only when needed, and get explained on the
  spot. Plain doesn't mean vague: risks are still stated directly. *Why:* if people
  can't follow what the AI did, their review becomes a rubber stamp.
  (In RULES.md: "Plain English, always")
- **Keep checking the work still serves the goal.** Before each step, the AI asks
  whether it actually moves the agreed goal forward, and stops and says so if not. If
  the plan itself turns out wrong, the plan gets changed openly. *Why:* the typical AI
  failure isn't bad code but busy, irrelevant work while the real goal goes untouched.
  (In RULES.md: "Check altitude every turn — does this still serve the spec?")

## Infrastructure

- **Domain settings live in code, not in a website's control panel.** The company you
  bought a domain from does two things only: points it at a managed DNS service and holds
  the one security record; it is a different company from that service, so one can still
  be changed when the other is down (a well-known login provider lost two and a half hours
  in 2026 because theirs were the same company). Every setting after that
  is changed there, reviewably, by the AI. If a domain still needs manual edits, move
  it properly, email settings included, and check mail still works before switching.
  *Why:* hand-edited settings in a web page are invisible, unreviewed and easy to break.
  (In RULES.md: "DNS lives in code, not in a registrar's web UI")

## How agents work

- **Write the hard rules down for the AI.** Each repo's instruction file spells out its
  must-follow rules, especially the knowledge that lives only in one person's head.
  When the AI hits a surprise, it records it there. *Why:* the AI can't know what was
  never written down. (In RULES.md: "Executable constraints in `CLAUDE.md`")
- **A second AI tries to prove the work wrong.** A separate reviewer, of a different make
  from the AI that wrote the change, looks for ways it is wrong, unsafe or incomplete.
  Every finding must point to the exact file and line or it doesn't count, and after the
  first round only serious findings are raised. The two go back and forth until it's
  resolved, until a round turns up nothing new, up to about five rounds, or until a person
  decides. Running the reviewer is part of the job, not something to ask permission for.
  If it didn't run, the AI says so. *Why:* the author of a change is the worst judge of
  it, and a reviewer of the same make shares its blind spots.
  (In RULES.md: "Adversarial reviewer agent")
- **Check harder where mistakes cost more.** Review depth depends on what a mistake would
  cost and whether it can be undone. Money, anything irreversible, logins and
  live customer-facing features get the full review. A change behind an on/off switch
  gets a lighter one. Wording and layout just ship and get looked at. A tiny change
  still counts: one small line once emptied a live shop's catalogue. *Why:* too little
  review breaks things, too much wastes time while looking diligent.
  (In RULES.md: "Scale the gate to the blast radius")
- **Safety checks must be automatic, not requests.** Anything that must block progress is
  an automatic check the AI can't talk its way past, not an instruction it's asked to
  follow. Only simple, reliable checks can block; AI opinions can advise but never
  decide pass or fail. A check on commands must look at what will actually run, not
  just the typed text. A hook (a small script that runs around the AI's actions) is not a
  hard stop either: if it runs out of time it lets the action through unless set to block.
  *Why:* instructions get ignored or tricked; automatic checks don't.
  (In RULES.md: "Gates as code, not prompts")
- **Produce a fixed plan, then run it the same way every time.** The AI writes a checked
  plan or configuration file, and that file runs without the AI improvising each
  time. *Why:* results are repeatable and cheap to re-run.
  (In RULES.md: "Deterministic artifacts over runtime improvisation")
- **Make the idea-to-release steps enforced, not optional** *(an aim, not yet in
  place)*. Every change moves through fixed stages (sorted, planned, reviewed,
  approved, built, merged, done) and can't skip one. Its progress is saved in the
  issue list so it survives between sessions. *Why:* skipped steps are where mistakes
  slip through. (In RULES.md: "Encode the idea→merge flow as an enforced state machine")
- **Tests are the final word.** The AI must never weaken a test to make it pass; it
  fixes the code instead. Before release, the finished product is used like a real
  user would, deliberately tried to break, and checked for speed. *Why:* passing the
  small tests isn't the same as working; one team shipped three bugs that passed all of
  theirs. (In RULES.md: "Tests are the source of truth")
- **Never live with a test that sometimes fails.** A test that passes and fails at random
  gets fixed or deleted straight away, never re-run until it happens to pass. *Why:*
  the AI learned from people who ignore these, and it will too unless this is enforced.
  (In RULES.md: "Never tolerate a flaky test")
- **Run AI jobs on a schedule, safely.** Recurring AI tasks like sorting issues, tidying
  up, finding faults, accessibility checks and docs run automatically. Each is locked
  down to read-only and can only suggest (one issue or one proposed change), never
  apply or merge on its own. The tools now offer the opposite, a "merge it yourself"
  switch and scheduled runs with every connected service open: the switch stays off, and
  a scheduled run only counts as safe once its connections are cut back to what it needs
  to read. *Why:* steady background upkeep, without handing over the keys.
  (In RULES.md: "Continuous AI — a third pillar beside CI/CD")
- **Start small.** Turn one habit into a rule, run the whole process once, and let what
  breaks tell you the next rule. *Why:* pointing AI at a whole repo at once and hoping
  doesn't work. (In RULES.md: "Start tiny")
- **Never give the same feedback twice.** Every repeated correction, incident or failed
  build becomes an automatic check so it can't happen again. *Why:* a correction that
  lives only in a conversation will be needed again.
  (In RULES.md: "Never give the same feedback twice")
- **Do things in parallel by default.** Split work into independent pieces and have
  several AI sessions work on them at once. Go one-at-a-time only when pieces touch
  the same files, depend on each other, or wait on a design decision. Keep each batch
  small enough for the checks to keep up. Parallel means each session in its own separate
  copy of the repo, never Claude Code's "agent teams", which share one copy and wave each
  other's plans through; a team-mate is never the one who reviews. *Why:* AI time is cheap
  and waiting isn't. The real limit is how fast work can be checked, not how many agents
  you can start. (In RULES.md: "Parallelise by default")
- **Each agent works in its own copy, which is tidied away afterwards.** Every parallel
  AI session gets its own separate working copy of the repo, called a worktree, kept
  in a hidden folder inside the repo. Before creating one, it checks for existing
  unfinished work and resumes that instead. Once the work is merged the copy is
  removed. A copy made by another session is never force-deleted; a leftover of your own
  that Claude Code kept because it had unsaved changes is checked and then removed, as
  its own instructions say. *Why:* two agents in one folder overwrite each other, and
  leftover copies pile up into confusion.
  (In RULES.md: "Isolated environment per agent — reconcile before you create it, close it when you finish")
- **Save progress every turn; don't rely on a clean exit.** Unfinished work is saved and
  uploaded after each step, with a note saying what to do next. The start of the next
  session is the real safety net: it shows anything left unsaved. *Why:* sessions crash
  or get closed, and work that only exists on one screen is lost.
  (In RULES.md: "Checkpoint before the turn ends; never trust the exit")
- **Build tools the AI can use well.** Tools are few and broad, loaded only when needed,
  rather than many narrow ones; each has a clear name and description, returns
  predictable results, and gives error messages the AI can learn from. Tools that delete
  are kept separate from tools that draft by our own checks, not by the tool's own
  say-so, and the AI never gets a tool it shouldn't use. *Why:* a confusing tool leads to
  confident mistakes, and too many tools crowd out the work.
  (In RULES.md: "Design tools/skills for the agent")
- **Reviewers look at the finished result, not the author's story of it.** A serious
  review reads the code as it would be after the change, with the whole repo in view, and
  is not shown the author's title, description or commit messages. *Why:* the author's
  framing nudges the reviewer into accepting the author's approach, and reading only the
  edited lines misses bugs that span files.
  (In RULES.md: "Review the merged result with the whole repo in view, withholding the author's framing")
- **The lead AI must be a strong model.** Cheap, small models are fine for low-stakes
  helper jobs, never for the AI in charge. *Why:* the lead makes the decisions everything
  else follows. (In RULES.md: "Don't let weak models drive the top-level agent")
- **One agent by default; a helper only for separate work or a second opinion.** Splitting
  a job that is really one chain of steps across several AIs costs up to ten times more and
  does worse. Add a helper only when the pieces are genuinely independent, or when a second
  AI of a different make must judge the first, and only if it measurably helps. Every agent
  runs visibly with only the access it needs. *Why:* more agents is not more capability; it
  is more cost and more handoffs. (In RULES.md: "Default to one agent; add a scoped helper only for independent work or a separate reviewer")
- **AI signs its own work.** An AI running on GitHub's or Anthropic's cloud saves changes
  under its own name, signed, with a link to the record of its session. Claude Code on a
  developer's machine cannot do that: its changes are in the person's name with a "co-authored by
  Claude" line, and that line is the record. Branches are merged in a way that keeps those
  lines (never "squashed"). *Why:* you can always tell who, or what, made a change.
  (In RULES.md: "Agents commit under their own identity")
- **Everything the AI does is logged and undoable.** *Why:* if you can't explain or
  reverse what an agent did, it shouldn't be near anything live. (In RULES.md: "Audit + rollback")
- **Error messages are written for the AI to act on.** Logs and failures are structured
  and name the problem with a link to how to fix it, so the AI can sort it out itself.
  *Why:* the AI is the one diagnosing and fixing, so it needs to understand the error.
  (In RULES.md: "Logs (and lint/test failures) are for the agent, not the human")
- **Knowledge about live systems is written down where the AI can look it up.** For
  anything running for real: what the services are, their settings, past incidents and
  where the logs go. *Why:* otherwise it's tribal knowledge the AI can't reach.
  (In RULES.md: "Production context is a first-class, queryable artifact")
- **Be able to switch AI providers.** Use tooling that lets you change AI company
  quickly, and treat being tied to one as a deliberate, written-down choice. Don't build
  AI calls into the product without deciding to, and re-test across models from time to
  time. When a new model arrives, re-test the whole setup around it, not just the model,
  and remove parts that only existed to prop up the old one. *Why:* models and prices
  change fast, and lock-in happens quietly, these days in the setup more than the model.
  (In RULES.md: "Swappable harness; deliberate provider coupling")

## Context and memory

- **Don't waste the AI's attention.** What the AI reads at the start of every session is
  kept short: a map pointing to detail, not the detail itself. Anthropic's guide is under
  200 lines per instruction file, and a file is loaded once, never also through a second
  route (the rules used to load twice in every repo). While working, it
  doesn't re-read files it already has, reads only the part it needs, hands big
  searches to a helper and keeps just the answer, and does independent steps together.
  *Why:* everything the AI reads costs money and time, and too much makes it worse,
  not better. (In RULES.md: "Token efficiency — lean context, lean habits")
- **Anything worth remembering goes in the repo, not the AI's private memory.** Rules,
  decisions, preferences and lessons are saved as files in the repo. The AI's own
  per-computer memory is switched off, including the newer side doors: helper agents'
  own memories, and memory moved to another folder. *Why:* private memory isn't reviewed or shared,
  no person can see it, it's lost with the machine, and it goes out of date without
  anyone noticing. (In RULES.md: "Durable knowledge lives in the repo, never in private memory")
- **One issue, one file, in the repo.** Every problem spotted, including ones not being
  worked on, is written down straight away as its own small file saying its status,
  why it matters and the next step. The AI adds, moves and lists issues with one standard
  command, so the files stay well-formed. *Why:* issues mentioned in a conversation get
  lost, and one shared list breaks when several agents edit it at once.
  Beside the tracker, one short working list says what is running and what is waiting right
  now, updated by the coordinating AI session every time something starts, finishes or is decided, so
  nothing drops off while several things run at once. (In RULES.md: "One issue, one file, in the repo")
- **Keep a record of every AI session.** Claude Code deletes session records after a
  month unless told otherwise, so the kit tells it to keep them and, where the optional
  archive hook is switched on, also copies each one to a private folder on the machine
  when the session ends. The copies stay on that
  machine, never in the repo, and only that machine's owner reads them: a session record contains
  code, command output and everything the AI read. *Why:* they're the raw material for
  improving the AI's skills later; that is our reason, not something the vendors advise.
  (In RULES.md: "Retain all agent sessions end-to-end")
- **Design and product knowledge matters too.** Much of what the AI needs lives outside
  the code: design systems, accessibility rules, reasons not to build something. Boil
  that down to what's useful and test that it helps. Tell product people how much
  effort things take so they can decide what not to build. Design and planning tools now
  plug straight into the AI; plug them in read-only where that is offered, and treat the
  rest as access grants. *Why:* code alone doesn't say what the product should be.
  (In RULES.md: "Product/design context is first-class")

## Skills

- **Skills are treated like code.** A skill is a packaged set of instructions the AI can
  load. Each does one job, is saved in the repo, is checked automatically, and comes
  with tests showing it works and gets used at the right moments. Third-party skills
  are extended, not edited. Skills are never installed on the account or the machine:
  one installed there quietly wins over a repo skill with the same name, and claude.ai
  now copies account skills onto the machine unless that is switched off. The skill's
  name must match its folder name, as the open standard requires. *Why:* a skill
  changes how the AI behaves, so it needs the same care as code. (In RULES.md: "Skills are code")

## Security

- **Give the least access that does the job.** Agents, connected tools and skills get
  only what their task needs: read-only where possible, no passwords. *Why:* whatever
  access an AI has can be misused by it or through it. (In RULES.md: "Least privilege")
- **Watch for the dangerous combination.** An agent that can see private data, reads
  content from outsiders, and can send things out can be tricked into leaking. If all
  three are present, remove one. Check across everything the agent is connected to,
  not one tool at a time. *Why:* the three parts usually sit in different tools, which
  makes the danger easy to miss. (In RULES.md: "Lethal-trifecta check")
- **Never let an AI that can run commands read material from outsiders.** Someone
  else's code, a web page, a sent file: any of them can carry hidden instructions that
  trick the AI into running them. This year's real attack started with "summarise this
  web page" and ended with the attacker's program running. Either take away the AI's
  ability to run things, or don't give it the outside material. *Why:* approval prompts
  and safety filters are both known to fail here.
  (In RULES.md: "Never point a code-executing agent at untrusted content")
- **Connected tools are access grants; limit them in their settings.** Every service
  connected to the AI starts read-only, limited to one project and to the features
  actually needed. Those limits live in the connection settings, where the AI can't
  argue past them. Widening access is always a deliberate decision.
  *Why:* an instruction telling the AI to be careful is not a lock.
  (In RULES.md: "MCP servers are privilege grants — scope them in the connection, not the prompt")
- **Passwords and keys never reach the AI.** Logins are handled separately and the AI
  only gets the ability they unlock. *Why:* anything the AI can see can end up in a log
  or a leak. (In RULES.md: "Keep secrets/tokens out of model context")
- **Check skills like any outside software.** Review everything a skill contains, not
  just its description, and re-check each update. Get software libraries from a source
  that scans them and waits for new releases to settle; no skill store does that yet, so
  a skill is pinned to one exact version and every update is re-read before it is taken.
  Some skill actions run before the AI even reads the skill, so "the AI will refuse" is
  not protection. *Why:* a skill is someone
  else's code running with your AI's access.
  (In RULES.md: "Vet skills like untrusted dependencies")
- **A person approves the risky actions.** Running commands, sending anything out, and
  anything that can't be undone need a human yes. Keep those prompts few enough that
  each is actually read. Where that's impossible, remove the ability rather than add
  another prompt. *Why:* people who click "approve" all day stop reading, and that's
  now the known way these safeguards fail. (In RULES.md: "Human gate on the dangerous legs")
- **Treat anything being reviewed as possibly hostile.** In any AI review, the change,
  its description and comments may contain attempts to manipulate the reviewer. Flag
  them, and give the reviewer read-only access. *Why:* hidden instructions in a change
  are a known attack. (In RULES.md: "Treat reviewed content as untrusted")
- **Check the automation itself.** Add a check that inspects the automatic build and
  release setup for security holes, loose permissions and exposed secrets. *Why:* once
  changes merge automatically, a weakness there is a weakness everywhere.
  (In RULES.md: "Review the pipeline itself")
- **Safety comes from walls around the AI, not instructions inside it.** Instructions
  given to the AI are advice, and they vanish when its conversation is cleared. Real
  protection sits outside it: a throwaway workspace, real passwords swapped in only
  at the last moment, and a list of the only places it may connect to. *Why:* the AI
  can be talked out of instructions but can't talk its way through a wall.
  (In RULES.md: "Isolate at the boundary, not in the prompt")
- **Protect shared memory.** When several agents share a store of knowledge, the shared
  part is read-only, each agent has its own scratch space, and changes can be rolled
  back. A withdrawn entry must be really deleted, not just marked withdrawn, because the
  AI keeps finding it otherwise and trusts it over the correction. *Why:* one bad or
  poisoned entry must not spread to every agent.
  (In RULES.md: "Protect shared memory")

## Getting better over time

- **Fix the cause, not just the mistake.** When the AI gets something wrong, improve the
  plan, instructions or checks so that kind of mistake can't happen again. Don't just
  patch the one result. *Why:* otherwise the same mistake returns in a new form.
  (In RULES.md: "Fix the system, not the code")
- **Schedule regular clean-up reviews.** Checks on each change miss the slow build-up of
  mess that fast AI work creates. So run periodic reviews of structure, outdated parts,
  security and whether a person can still explain how it works, and decide as a team what
  to act on; the AI's instruction files get the same review. *Why:* small shortcuts add
  up to a codebase that's hard to change, or that nobody understands.
  (In RULES.md: "Schedule drift/debt reviews ("garbage collection")")
