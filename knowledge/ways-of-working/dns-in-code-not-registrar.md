# DNS lives in code, not in a registrar's web UI

**Principle:** The registrar does exactly one job — point nameservers at a managed
zone. Every record after that is created and changed in the managed zone, by an
agent, reviewably. Never hand-edit a record at the registrar.

**Why:** A record typed into GoDaddy's web UI is unreviewable, unversioned, and
invisible to every later session — no agent can read it, diff it, or roll it back,
and nobody can say later why it exists. It is also the single most common way a
cutover silently breaks mail: the web UI's record list looks complete, the zone
that replaces it isn't, and MX/SPF/DKIM/DMARC quietly stop resolving. Manual steps
also stall migrations: a runbook whose next action is "add this record at the
registrar" waits on a human every time, so the migration never finishes.

**How to apply:**

- **Registrar scope:** nameserver delegation only. Nothing else is set there, ever.
- **Everything else** — A/AAAA, CNAME, TXT, MX, SRV, CAA — is defined in the managed
  zone (Cloud DNS or equivalent) and changed the same way as any other change: an
  agent makes it, it's reviewable, it's revertable.
- **Never write a runbook step that says "add this record at GoDaddy."** If a domain
  still needs one, that's the signal the zone hasn't been migrated. The correct next
  action is to migrate the zone, not to do the manual edit.
- **Migrating a zone means replicating _every_ existing record first** — walk the
  registrar's full record list, MX and SPF/DKIM/DMARC included, into the managed
  zone. Then **verify mail actually flows** (send and receive, check the SPF/DKIM
  pass) **before** you repoint the nameservers. Delegating first and fixing records
  afterwards is what breaks mail.
- **Treat delegation as the irreversible step:** it takes effect at TTL speed and
  isn't undone by a `git revert`. Confirm the replicated zone answers correctly
  (query it directly by nameserver) before switching.

**Source:** Adopted 2026-07-27, after a domain migration repeatedly stalled on manual
registrar steps. Not from a conference talk — this one is from our own incident.
