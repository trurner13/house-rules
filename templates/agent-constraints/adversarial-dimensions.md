# Adversarial review dimensions

The adversarial reviewer challenges every plan/change across these dimensions and
tries to **prove it's wrong, unsafe, or incomplete**. Loop planner ↔ reviewer with
a hard cap (~5 rounds); if they can't converge, escalate to a human. Adapt per repo.

## Architecture

Does it fit the system's architecture and domain boundaries? Right abstraction
level? Is there a better, already-established pattern? Check the repo's design docs.

## Scope

Too much or too little? Does it match the issue/spec? Any scope creep or
unnecessary changes?

## Risk

Are all failure modes and edge cases identified — race conditions, backwards
compatibility, partial failures? Pay special attention to **state that persists
across a failure boundary**: if something mutates shared state before I/O that can
throw, does every failure path unwind it — and does the cleanup not shadow the
original error? (Silent failure: first error propagates, cleanup hits orphaned
state, cleanup's own failure hides the real one.)

## Testing

Is the test strategy sufficient? Edge cases covered? Integration-test gaps?
Over-reliance on unit tests? Are there end-to-end gaps that should be filed as UAT?

## Complexity

Over-engineered? Could it be simpler? Any unnecessary abstractions or indirection?

## Correctness

Will it actually solve the problem? Logical gaps? Does it match established
patterns in the codebase?

## Documentation

Does it change concepts, commands, or patterns that design docs / skills describe?
If so, the plan must include steps to update them. Flag any gaps as findings.
