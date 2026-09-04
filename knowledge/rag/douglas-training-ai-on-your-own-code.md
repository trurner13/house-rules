# Train a small model on your own agent sessions

**Principle:** Your day-to-day AI agent sessions are training data. Capture every session, mine the good ones for reusable skills, and (when it pays off) fine-tune a small local model on that data instead of always reaching for a frontier API.

**Why:** Frontier models are generic, costly per call, and send your code outside your walls. The work your agents already do on your codebase is the highest-quality, most specific dataset you will ever have — but it evaporates unless you record it. Without a capture pipeline you keep re-paying to re-teach the model the same context every time.

**How to apply:**
- **Put a recorder in front of the model.** Use a telemetry proxy (the talk's "tapes") that sits between your agent and the model and logs every session end-to-end — prompts, tool calls, responses, outcomes. Capture is automatic, not opt-in.
- **Run agents through a controlled runtime.** An agent runtime (the talk's "steros") executes sessions, including parallel agents, so traces are consistent and comparable.
- **Mine traces into skills, not just data.** Review captured sessions, find the ones that solved a problem cleanly, and extract the reusable pattern as a named skill — turning a one-off success into standing capability. See `skills-as-the-new-code`.
- **Only fine-tune when there's a real payoff** — a narrow, repeated task where a small local model beats paying for a frontier call each time. Use parameter-efficient methods like QLoRA so training runs on modest hardware.
- **Choose the training method by what data you have.** Use SFT (supervised fine-tuning) when you have clear correct examples of the behaviour you want. Use DPO (preference tuning) when you have pairs of better-vs-worse responses and want to nudge the model toward the preferred style.
- **Treat it as a loop:** capture → extract skills → fine-tune → the better agent generates better traces. Keep the data flywheel turning.

**Source:** Brian Douglas — "The beginner's guide to training AI on your own code", AI Native DevCon London, June 2026. [Talk skill](https://tessl.io/registry/ainativedev/aidevcon-2026-ldn/files/talk-douglas-training-ai-on-your-own-code/SKILL.md)
