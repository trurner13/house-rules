// Internal-link gate: every relative markdown link in the curated docs must
// resolve to a real file/dir. Deterministic, no network. Excludes transcripts/
// and scratch. Run: node scripts/check-links.mjs   (exit 1 if any link is broken)
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve, relative } from "node:path";

const ROOT = resolve(".");
const SKIP = new Set(["transcripts", ".specs-raw", ".git", "node_modules"]);
const linkRe = /!?\[[^\]]*\]\(([^)]+)\)/g;

function walk(dir) {
  let out = [];
  for (const name of readdirSync(dir)) {
    if (SKIP.has(name)) continue;
    const p = join(dir, name);
    const s = statSync(p);
    if (s.isDirectory()) out = out.concat(walk(p));
    else if (name.endsWith(".md")) out.push(p);
  }
  return out;
}

const broken = [];
for (const file of walk(ROOT)) {
  const text = readFileSync(file, "utf8");
  let m;
  while ((m = linkRe.exec(text))) {
    let target = m[1].trim();
    if (/^(https?:|mailto:|#|tel:)/i.test(target)) continue; // external / anchor-only
    target = target.split("#")[0].replace(/:\d+$/, "").trim();  // drop #anchor and :line
    if (!target) continue;
    const abs = resolve(dirname(file), target);
    if (!existsSync(abs)) broken.push(`${relative(ROOT, file)}  ->  ${m[1]}`);
  }
}

if (broken.length) {
  console.error(`BROKEN internal links (${broken.length}):`);
  broken.forEach((b) => console.error("  " + b));
  process.exit(1);
}
console.log("OK: all internal markdown links resolve.");
