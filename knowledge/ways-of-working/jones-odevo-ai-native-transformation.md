# Earn the right to roll out agentic coding

**Principle:** Don't hand developers AI licences and hope. Get your fundamentals in order first, then run a structured rollout — discovery, in-person workshops, a small pilot, training, and train-the-trainer — and expect to redesign how you build once adoption lands.

**Why:** Licences and training alone don't move the needle. If your delivery is shaky, AI makes it worse, not better — the 2025 DORA finding the speakers cite is blunt: if you aren't doing software development well and you throw agentic coding at the problem, things get worse. Agents amplify whatever system they land in. And when one part of the system speeds up, the bottleneck just moves downstream (at Odevo it shifted from engineering to product), so plan for that.

**How to apply:**
- **Check the prerequisites before training anyone.** Four hard gates, plus measurement:
  - *CI/CD* — if you can't ship reliably and quickly, agents won't fix that.
  - *Platform* — without one you can't ship code dependably.
  - *Tests* — "if agents can't run tests to find out they've broken your software, don't be surprised when they break your software."
  - *Coding standards* — if humans don't agree what good looks like, an agent has little chance of producing code the team will approve.
  - *Transparency / flow measurement* — Odevo spent ~18 months making delivery visible before they trained anyone.
- **Run the rollout as a playbook:** discovery → in-person workshops → small pilot → broad training → train-the-trainer (so the capability spreads without you).
- **Make workshops surface fears, not just skills.** Use liberating-structures and TRIZ exercises (e.g. "200 junior devs who never sleep"); run the first half in person with no laptops; feed people; debrief with "what did we just do?".
- **Buy training deliberately.** Their RFP required paid discovery, in-person delivery, and train-the-trainer capability (80 submissions, shortlisted 10, picked 3).
- **Teach the real syllabus:** context windows and maximum effective context window, failure modes and hallucination, spec-driven development, MCP, multi-agent workflows. See `context-window-management` and `spec-driven-development`.
- **Expect to reinvent the SDLC** once adoption is real; watch for the new downstream bottleneck and AI-induced overwork.

**Source:** Daniel Jones (re-cinq) and Tomasz (Odevo) — "More software, faster — Odevo's AI Native transformation", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-jones-odevo-ai-native-transformation/SKILL.md)
