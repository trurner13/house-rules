# Treat Agent Skills as Untrusted Supply Chain

**Principle:** Agent "skills" are executable code shipped with no security model — no sandboxing, signing, lockfiles, or integrity checks. Review and contain them with the same suspicion you'd apply to a random NPM package, and watch for the "lethal trifecta" of capabilities that turns a benign agent into an exfiltration tool.

**Why:** Skills are spreading to developers at roughly 10x the speed NPM did circa 2015, but without any of the supply-chain hygiene the ecosystem eventually grew. Snyk scanned ~4,000 skills on Glow and found roughly 1 in 3 had security issues. A skill that looks helpful can quietly read your secrets, install other skills (confused-deputy), or hide payloads in invisible characters. With no integrity layer, the only defense is human judgment — and that judgment erodes under acceptance fatigue.

**How to apply:**
- **Check for the lethal trifecta (toxic flows).** Risk compounds when an agent simultaneously has: (1) access to private data, (2) exposure to untrusted content, and (3) an external communication channel to send data out. Any one alone is survivable; all three together is the danger. Audit every skill/agent setup against these three dimensions, treating *memory* and *shell access* as amplifiers that widen the blast radius.
- **Break the trifecta deliberately.** If a skill needs private data, deny it the outbound channel — or vice versa. Remove one leg and the toxic flow collapses.
- **Review skills like dependencies.** Read what a skill actually does before installing. Watch for the documented attack patterns: malicious "skill scanner" tools, fake deployment skills, "buy anything" skills, and Trojan Source attacks that hide instructions in invisible Unicode characters your eyes can't see but the model reads.
- **Beware the confused deputy.** A skill can use your authority to install or trigger other skills you never approved. Don't let one accepted skill become a gateway.
- **Fight acceptance fatigue.** Each "Allow?" prompt you rubber-stamp lowers your guard. Slow down on permission grants; don't run agents in unrestricted (YOLO) mode against anything sensitive.
- **Push for the missing controls:** sandboxing, signing, and lockfiles. Until the ecosystem has them, you are the integrity check.

See also `talk-tal-skills-security` context on `skills` authoring and `mcp` security.

**Source:** Liran Tal (Snyk) — "Skills Security", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-tal-skills-security/SKILL.md)
