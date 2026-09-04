// Leanness gate for rules/RULES.md — it loads in every session of every repo, so
// it must stay lean: one-ish line per rule, and not balloon into a dump. If a rule
// needs more, the detail belongs in knowledge/ or agent-constraints/, not here.
// Run: node scripts/check-rules-lean.mjs   (exit 1 on violation)
import { readFileSync } from "node:fs";

const MAX_RULE_CHARS = 850; // a single rule (incl. its wrapped lines) must stay short
const MAX_RULES = 60;       // a soft ceiling — past this, prune or move detail to knowledge/

const lines = readFileSync("rules/RULES.md", "utf8").split(/\r?\n/);
const starts = [];
lines.forEach((l, i) => { if (/^- \*\*/.test(l)) starts.push(i); });

const violations = [];
for (let k = 0; k < starts.length; k++) {
  const start = starts[k];
  let end = lines.length;
  for (let j = start + 1; j < lines.length; j++) {
    if (/^- |^## |^> /.test(lines[j])) { end = j; break; }
  }
  const block = lines.slice(start, end).join(" ").replace(/\s+/g, " ").trim();
  if (block.length > MAX_RULE_CHARS) {
    violations.push(`rule too long (${block.length} > ${MAX_RULE_CHARS}): ${block.slice(0, 60)}…`);
  }
}
if (starts.length > MAX_RULES) {
  violations.push(`too many rules (${starts.length} > ${MAX_RULES}) — prune or move detail to knowledge/`);
}

console.log(`RULES.md: ${lines.length} lines, ${starts.length} rules.`);
if (violations.length) {
  console.error("LEAN CHECK FAILED:");
  violations.forEach((v) => console.error("  " + v));
  process.exit(1);
}
console.log("OK: RULES.md is lean.");
