# How to add knowledge

One idea per file. Filename in `kebab-case.md`. Drop it in the matching
`knowledge/<topic>/` folder. Use this template:

```markdown
# <Short title of the practice>

**Principle:** <the one-sentence rule of thumb>

**Why:** <the reasoning / what goes wrong without it>

**How to apply:** <concrete steps, examples, or a snippet>

**Source:** <where I learned it — talk, person, link, date>
```

If the practice is important enough to apply to *every* AI task, also add a
one-line summary to `rules/RULES.md` that links back to this file.

## How a rule gets adopted: on trial in a real repo, never from a list

There is no parked list of candidate rules (a parked list of candidates goes unused,
because only `rules/RULES.md` is vendored). A rule earns its place like this:

1. **Start it where the problem showed.** Write it as a repo-specific constraint in that
   repo's `.claude/rules/<name>.md`, headed "on trial from <date>", in plain English, with
   the evidence that prompted it. It is in force in that repo from the next session.
2. **Give it a number.** The session-start digest (or a hook) prints the measure that says
   whether the rule is holding - a count, an age, a pass/fail - so the review has evidence,
   not a recollection.
3. **Track it in the source repo's tracker**, with the review date.
4. **Decide on the date.** Adopt it (one line in `rules/RULES.md`, the full note in
   `knowledge/`, re-sync everywhere) or drop it and record why.

## Why two layers?

`rules/RULES.md` is loaded into context in **every** AI session everywhere, so it
must stay short. The `knowledge/` files hold the full detail and are only read
when the topic is actually relevant — so they can be as long as you want.
