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

## Why two layers?

`rules/RULES.md` is loaded into context in **every** AI session everywhere, so it
must stay short. The `knowledge/` files hold the full detail and are only read
when the topic is actually relevant — so they can be as long as you want.
