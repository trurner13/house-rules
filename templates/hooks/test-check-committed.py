"""Red-then-green harness for check-committed.py.

Builds throwaway git repos, each engineered to fail (or pass) exactly one way, and
asserts on the CODES the checker emits -- so every check is watched failing before
it is trusted passing. Stdlib only; no network.

    python templates/hooks/test-check-committed.py

It has already earned its keep twice: it caught an escape hatch that worked on only
some paths, and a str.lstrip("./") that strips a CHARACTER SET and so ate the leading
dot of every dotfile -- which is most of the must-ship list.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = (Path(__file__).resolve().parent / "check-committed.py")
results: list[tuple[bool, str, str]] = []


def sh(cwd: Path, *args: str) -> None:
    subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def new_repo(tmp: Path, name: str) -> Path:
    root = tmp / name
    root.mkdir(parents=True)
    sh(root, "git", "init", "-q", "-b", "main", ".")
    sh(root, "git", "config", "user.email", "t@example.com")
    sh(root, "git", "config", "user.name", "t")
    return root


def write(root: Path, rel: str, body: str = "x\n") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def run(root: Path, *extra: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--json", *extra],
        capture_output=True, text=True,
    )
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"_stdout": proc.stdout, "_stderr": proc.stderr}


def codes(payload: dict, key: str = "problems") -> set[str]:
    return {p["code"] for p in payload.get(key, [])}


def expect(label: str, condition: bool, detail: str = "") -> None:
    results.append((condition, label, detail))
    print(("  PASS  " if condition else "  FAIL  ") + label + (f"   [{detail}]" if detail else ""))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cc-test-"))
    try:
        # --- 1. the real-world failure: a blanket .claude/ hides the whole kit -------
        r = new_repo(tmp, "blanket")
        write(r, ".claude/rules/00-guardrails.md")
        write(r, ".claude/settings.json", "{}\n")
        write(r, ".gitignore", ".claude/\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("blanket .claude/ is caught", rc == 1 and "IGNORED_MUST_SHIP" in codes(out),
               ",".join(sorted(codes(out))))
        hit = [p for p in out.get("problems", []) if "settings.json" in p["path"]]
        expect("names the exact rule hiding it",
               bool(hit) and hit[0].get("pattern") == ".claude/",
               hit[0].get("pattern") if hit else "no hit")

        # --- 2. the negation that cannot work -------------------------------------
        r = new_repo(tmp, "negation")
        write(r, ".claude/rules/00-guardrails.md")
        write(r, ".gitignore", ".claude/\n!.claude/rules/\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("broken '!' negation is caught", "BROKEN_NEGATION" in codes(out),
               ",".join(sorted(codes(out))))

        # green: the correct form clears it
        r2 = new_repo(tmp, "negation-fixed")
        write(r2, ".claude/rules/00-guardrails.md")
        write(r2, ".gitignore", ".claude/*\n!.claude/rules/\n")
        sh(r2, "git", "add", "-A")
        sh(r2, "git", "commit", "-qm", "init")
        rc2, out2 = run(r2)
        expect("correct 'dir/*' form passes", rc2 == 0 and not out2["problems"],
               ",".join(sorted(codes(out2))))

        # --- 2b. the fuse: files already committed, but the DIRECTORY is ignored.
        #         Nothing looks broken today; every file added from now on vanishes.
        r = new_repo(tmp, "latent-dir")
        write(r, ".claude/rules/00-guardrails.md")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("a tracked kit with no ignore rule is clean", rc == 0, f"rc={rc}")
        write(r, ".gitignore", ".claude/\n")
        rc, out = run(r)
        expect("ignoring the DIRECTORY of already-tracked files is still caught",
               rc == 1 and "IGNORED_MUST_SHIP_DIR" in codes(out),
               ",".join(sorted(codes(out))))
        write(r, ".gitignore", ".claude/*\n!.claude/rules/\n")
        rc, out = run(r)
        expect("the contents form clears the fuse", rc == 0, f"rc={rc}")

        # --- 3. the handover killer: a rule that lives on ONE machine -------------
        r = new_repo(tmp, "machine-local")
        write(r, "package-lock.json", "{}\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "README.md")
        sh(r, "git", "commit", "-qm", "init")
        (r / ".git" / "info").mkdir(parents=True, exist_ok=True)
        (r / ".git" / "info" / "exclude").write_text("package-lock.json\n", encoding="utf-8")
        rc, out = run(r)
        expect("ignore rule in .git/info/exclude is flagged as machine-local",
               "MACHINE_LOCAL_IGNORE" in codes(out), ",".join(sorted(codes(out))))

        # --- 4. global excludesFile: invisible in the repo, absent from every clone -
        r = new_repo(tmp, "global-exclude")
        gitignore_global = tmp / "gitignore_global"
        gitignore_global.write_text(".editorconfig\n", encoding="utf-8")
        sh(r, "git", "config", "core.excludesFile", str(gitignore_global))
        write(r, ".editorconfig", "root = true\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "README.md")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("machine-global excludesFile is flagged as machine-local",
               "MACHINE_LOCAL_IGNORE" in codes(out), ",".join(sorted(codes(out))))

        # --- 5. exists, not ignored, simply never added ----------------------------
        r = new_repo(tmp, "untracked")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "README.md")
        sh(r, "git", "commit", "-qm", "init")
        write(r, "poetry.lock", "[[package]]\n")
        rc, out = run(r)
        expect("never-committed lock file is caught",
               "UNTRACKED_MUST_SHIP" in codes(out), ",".join(sorted(codes(out))))

        # --- 6. '.env*' eats the example --------------------------------------------
        r = new_repo(tmp, "env-eaten")
        write(r, ".gitignore", ".env*\n")
        write(r, ".env", "SECRET=1\n")
        write(r, ".env.example", "SECRET=\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("'.env*' hiding .env.example is caught",
               "IGNORED_MUST_SHIP" in codes(out), ",".join(sorted(codes(out))))

        # --- 7. a .env with no committed example at all -----------------------------
        r = new_repo(tmp, "no-example")
        write(r, ".gitignore", ".env\n")
        write(r, ".env", "SECRET=1\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("missing .env.example is an advisory locally",
               rc == 0 and "MISSING_COUNTERPART" in codes(out, "advisories"),
               f"rc={rc} " + ",".join(sorted(codes(out, "advisories"))))
        rc, out = run(r, "--ci")
        expect("--ci promotes the advisory to a failure",
               rc == 1 and "MISSING_COUNTERPART" in codes(out), f"rc={rc}")

        # --- 8. .must-commit: repo-specific additions and exemptions ----------------
        r = new_repo(tmp, "manifest")
        write(r, ".gitignore", "config/\n")
        write(r, "config/settings.yml", "a: 1\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "README.md", ".gitignore")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("unlisted project file is not flagged by default", rc == 0, f"rc={rc}")
        write(r, ".must-commit", "config/settings.yml\n")
        rc, out = run(r)
        expect(".must-commit adds a project's own must-ship file",
               rc == 1 and "IGNORED_MUST_SHIP" in codes(out), ",".join(sorted(codes(out))))
        write(r, ".must-commit", "config/settings.yml\n-config/settings.yml\n")
        rc, out = run(r)
        expect("a '-' line exempts it again", rc == 0, f"rc={rc}")

        # the realistic exemption: a repo that deliberately does not ship a built-in
        r = new_repo(tmp, "exempt-builtin")
        write(r, ".gitignore", ".vscode/\n")
        write(r, ".vscode/launch.json", "{}\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "README.md", ".gitignore")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("a hidden built-in must-ship file fails by default",
               rc == 1 and "IGNORED_MUST_SHIP" in codes(out), f"rc={rc}")
        write(r, ".must-commit", "-.vscode/launch.json\n")
        rc, out = run(r)
        expect("exempting a BUILT-IN clears it", rc == 0, f"rc={rc}")
        write(r, ".vscode/settings.json", "{}\n")
        write(r, ".must-commit", "-.vscode/\n")
        rc, out = run(r)
        expect("a directory exemption covers paths beneath it", rc == 0, f"rc={rc}")

        # --- 9. large ignored file must be documented, not silent -------------------
        r = new_repo(tmp, "big-file")
        write(r, ".gitignore", "data/\n")
        write(r, "README.md", "# r\n")
        (r / "data").mkdir()
        (r / "data" / "set.bin").write_bytes(b"0" * (12 * 1024 * 1024))
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("silent 12 MB ignored file is flagged",
               "UNDOCUMENTED_LARGE_IGNORED" in codes(out, "advisories"),
               ",".join(sorted(codes(out, "advisories"))))
        write(r, "README.md", "# r\n\n## What this clone can't give you\n\n- data/set.bin"
                              " (12 MB) - Drive: <link>. Ask Dana.\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "doc")
        rc, out = run(r)
        expect("documenting it in the README clears the flag",
               "UNDOCUMENTED_LARGE_IGNORED" not in codes(out, "advisories"),
               ",".join(sorted(codes(out, "advisories"))))

        # --- 10. a committed big file is the opposite mistake -----------------------
        r = new_repo(tmp, "big-tracked")
        write(r, "README.md", "# r\n")
        (r / "blob.bin").write_bytes(b"0" * (12 * 1024 * 1024))
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("a 12 MB COMMITTED file is flagged too",
               "LARGE_TRACKED_FILE" in codes(out, "advisories"),
               ",".join(sorted(codes(out, "advisories"))))

        # --- 11. a healthy repo passes cleanly --------------------------------------
        r = new_repo(tmp, "green")
        write(r, ".gitignore", ".claude/worktrees/\nnode_modules/\n.env\n")
        write(r, ".claude/rules/00-guardrails.md")
        write(r, ".claude/settings.json", "{}\n")
        write(r, ".claude/worktrees/scratch/x.txt")
        write(r, "package-lock.json", "{}\n")
        write(r, ".env.example", "KEY=\n")
        write(r, ".env", "KEY=real\n")
        write(r, ".editorconfig", "root = true\n")
        write(r, "README.md", "# r\n")
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "init")
        rc, out = run(r)
        expect("a healthy repo passes", rc == 0 and not out["problems"],
               ",".join(sorted(codes(out))) or "clean")
        expect("worktrees/ is not mistaken for a must-ship dir",
               "IGNORED_MUST_SHIP" not in codes(out))

        # --- 12. not a git repo at all ----------------------------------------------
        plain = tmp / "plain"
        plain.mkdir()
        rc, out = run(plain)
        expect("a non-repo is reported, not crashed", rc == 1 and "NOT_A_REPO" in codes(out),
               ",".join(sorted(codes(out))))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
