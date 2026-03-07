#!/usr/bin/env python3
"""Release automation for consolidation-memory.

Usage:
    python scripts/release.py 0.4.0           # bump, test, gate, commit, tag, push
    python scripts/release.py 0.4.0 --dry-run # show what would happen
    python scripts/release.py 0.4.0 --no-push # commit + tag but don't push
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_SCOPE_USE_CASE = "Drift-aware debugging memory"
NOVELTY_RELEASE_RESULT = ROOT / "benchmarks" / "results" / "novelty_eval_release_full.json"
RELEASE_GATE_REPORT = ROOT / "benchmarks" / "results" / "release_gate_report.json"


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(ROOT), check=check, capture_output=capture, text=True)


def get_current_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"(.+?)"', text, re.MULTILINE)
    if not match:
        sys.exit("Could not find version in pyproject.toml")
    return match.group(1)


def set_version(new_version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    text = re.sub(r'^(version\s*=\s*)"(.+?)"', rf'\1"{new_version}"', text, count=1, flags=re.MULTILINE)
    PYPROJECT.write_text(text, encoding="utf-8")


def add_changelog_header(new_version: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    today = date.today().isoformat()
    header = f"## {new_version} - {today}\n"

    marker = "# Changelog\n"
    if marker not in text:
        sys.exit("Could not find '# Changelog' header in CHANGELOG.md")

    if f"## {new_version}" in text:
        print(f"  Changelog already has entry for {new_version}, skipping header insertion")
        return

    text = text.replace(marker, f"{marker}\n{header}\n", 1)
    CHANGELOG.write_text(text, encoding="utf-8")


def rollback_version(current: str) -> None:
    print(f"  Rolling back version to {current}...")
    set_version(current)


def main() -> None:
    parser = argparse.ArgumentParser(description="Release consolidation-memory")
    parser.add_argument("version", help="New version (e.g. 0.4.0)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--no-push", action="store_true", help="Commit + tag but don't push")
    args = parser.parse_args()

    new_version = args.version

    if not PYPROJECT.exists():
        sys.exit(f"pyproject.toml not found at {PYPROJECT}")
    if not CHANGELOG.exists():
        sys.exit(f"CHANGELOG.md not found at {CHANGELOG}")

    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        sys.exit(f"Invalid version format: {new_version} (expected X.Y.Z)")

    current = get_current_version()

    print(f"\nRelease: {current} -> {new_version}")
    print(f"{'(DRY RUN)' if args.dry_run else ''}\n")

    result = run(["git", "status", "--porcelain"], capture=True)
    if result.stdout.strip():
        sys.exit("Working tree is not clean. Commit or stash changes first.")

    print("\n[1/7] Pulling latest from origin...")
    if not args.dry_run:
        run(["git", "pull", "--ff-only", "origin", "main"])

    print(f"\n[2/7] Bumping version: {current} -> {new_version}")
    if not args.dry_run:
        set_version(new_version)
        actual = get_current_version()
        if actual != new_version:
            sys.exit(
                f"Version substitution failed: expected {new_version}, "
                f"got {actual} in pyproject.toml"
            )

    print(f"\n[3/7] Adding changelog header for {new_version}")
    if not args.dry_run:
        add_changelog_header(new_version)
    print("  -> Edit CHANGELOG.md now to add release notes, then re-run without --dry-run")
    print("     Or add notes before running this script.")

    print("\n[4/7] Reinstalling and running tests...")
    if not args.dry_run:
        run([sys.executable, "-m", "pip", "install", "-e", ".[fastembed,dev]", "--quiet"])
        result = run([sys.executable, "-m", "pytest", "tests/", "-v"], check=False)
        if result.returncode != 0:
            rollback_version(current)
            sys.exit("Tests failed - aborting release. Version reverted. Fix failures and re-run.")
        result = run([sys.executable, "-m", "ruff", "check", "src/", "tests/"], check=False)
        if result.returncode != 0:
            rollback_version(current)
            sys.exit("Lint check failed - aborting release. Version reverted. Fix lint errors and re-run.")

    print("\n[5/7] Running release gate checks...")
    if not args.dry_run:
        NOVELTY_RELEASE_RESULT.parent.mkdir(parents=True, exist_ok=True)

        result = run(
            [
                sys.executable,
                "-m",
                "benchmarks.novelty_eval",
                "--mode",
                "full",
                "--output",
                str(NOVELTY_RELEASE_RESULT),
            ],
            check=False,
        )
        if result.returncode != 0:
            rollback_version(current)
            sys.exit("Full novelty evaluation failed - aborting release. Version reverted.")

        result = run(
            [
                sys.executable,
                "scripts/verify_release_gates.py",
                "--novelty-result",
                str(NOVELTY_RELEASE_RESULT),
                "--scope-use-case",
                RELEASE_SCOPE_USE_CASE,
                "--output",
                str(RELEASE_GATE_REPORT),
            ],
            check=False,
        )
        if result.returncode != 0:
            rollback_version(current)
            sys.exit(
                "Release gate verification failed - aborting release. "
                "Version reverted. See benchmarks/results/release_gate_report.json."
            )

    print(f"\n[6/7] Committing v{new_version}...")
    if not args.dry_run:
        run(["git", "add", "pyproject.toml", "CHANGELOG.md"])
        run(["git", "commit", "-m", f"v{new_version}"])
        run(["git", "tag", f"v{new_version}"])

    if args.no_push:
        print("\n[7/7] Skipping push (--no-push). Run manually:")
        print(f"  git push origin main v{new_version}")
    elif args.dry_run:
        print(f"\n[7/7] Would push main + tag v{new_version}")
    else:
        print(f"\n[7/7] Pushing main + tag v{new_version}...")
        run(["git", "push", "origin", "main", f"v{new_version}"])

    print(f"\nDone! v{new_version} {'would be' if args.dry_run else 'is'} released.")
    if not args.dry_run and not args.no_push:
        print(f"PyPI publish will trigger from the v{new_version} tag via GitHub Actions.")


if __name__ == "__main__":
    main()
