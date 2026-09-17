#!/usr/bin/env python3
"""Escanea archivos de texto y emite hallazgos de secrets como JSON.

Exit codes: 0 sin hallazgos/ayuda, 1 con hallazgos, 2 uso invalido.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS = [
    ("AWS Access Key", r"AKIA[0-9A-Z]{16}", "high"),
    ("AWS Secret Key", r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}", "high"),
    ("GitHub Token", r"(?:ghp_|gho_)[A-Za-z0-9]{36}", "high"),
    ("GitHub Fine-grained Token", r"github_pat_[A-Za-z0-9_]{82}", "high"),
    ("GitLab Token", r"glpat-[A-Za-z0-9-]{20}", "high"),
    ("Slack Bot Token", r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}", "high"),
    (
        "Slack Webhook",
        r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}",
        "high",
    ),
    ("Stripe Secret Key", r"sk_live_[A-Za-z0-9]{24,}", "high"),
    ("Stripe Publishable Key", r"pk_live_[A-Za-z0-9]{24,}", "low"),
    ("SendGrid API Key", r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}", "high"),
    ("Google API Key", r"AIza[0-9A-Za-z_-]{35}", "high"),
    ("npm Token", r"npm_[A-Za-z0-9]{36}", "high"),
    ("PyPI Token", r"pypi-[A-Za-z0-9_-]{50,}", "high"),
    ("Private Key", r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----", "medium"),
    ("Generic Password", r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "medium"),
    (
        "Generic Secret",
        r"(?i)(?:secret|token|api_key|apikey|access_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "medium",
    ),
    ("Connection String", r"(?i)(?:mongodb|postgres|mysql|redis)://[^:]+:[^@]+@", "medium"),
    ("JWT Hardcoded", r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "medium"),
]

COMPILED_PATTERNS = [(name, re.compile(pattern), confidence) for name, pattern, confidence in PATTERNS]
GENERIC_SECRET_TYPES = {"Generic Password", "Generic Secret"}
IGNORE_DIRS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}
IGNORE_EXTENSIONS = {
    ".lock",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".ico",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".mp3",
    ".mp4",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".jar",
    ".class",
}
IGNORE_COMPOUND_SUFFIXES = (".min.js", ".min.css")
IGNORE_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "Pipfile.lock",
    "poetry.lock",
    "composer.lock",
    "go.sum",
}
TEST_SUFFIXES = (
    ".test.js",
    ".test.ts",
    ".spec.js",
    ".spec.ts",
    "_test.py",
    "_test.go",
    ".example",
    ".sample",
    ".template",
)


def should_scan(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return False
    name = path.name.lower()
    return (
        path.is_file()
        and path.suffix.lower() not in IGNORE_EXTENSIONS
        and name not in IGNORE_FILENAMES
        and not name.endswith(IGNORE_COMPOUND_SUFFIXES)
    )


def is_test_file(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith(("test_", "spec_")) or name.endswith(TEST_SUFFIXES)


def scan_file(path: Path, root: Path) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    findings: list[dict[str, object]] = []
    test_file = is_test_file(path)
    for line_number, line in enumerate(lines, 1):
        line_matches: list[tuple[str, str]] = []
        for name, pattern, confidence in COMPILED_PATTERNS:
            if confidence == "medium" and test_file:
                continue
            if pattern.search(line):
                line_matches.append((name, confidence))

        if any(name not in GENERIC_SECRET_TYPES for name, _ in line_matches):
            line_matches = [
                match for match in line_matches if match[0] not in GENERIC_SECRET_TYPES
            ]
        findings.extend(
            {
                "type": name,
                "confidence": confidence,
                "file": path.relative_to(root).as_posix(),
                "line": line_number,
            }
            for name, confidence in line_matches
        )
    return findings


def requested_files(root: Path, from_stdin: bool) -> list[Path]:
    if not from_stdin:
        return [path for path in root.rglob("*") if should_scan(path)]
    files: list[Path] = []
    for raw in sys.stdin:
        candidate = (root / raw.strip()).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if should_scan(candidate):
            files.append(candidate)
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="lee paths relativos desde stdin")
    parser.add_argument("target_dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.target_dir.resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 2
    files = requested_files(root, args.stdin)
    findings = [finding for path in files for finding in scan_file(path, root)]
    rank = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: (rank.get(str(item["confidence"]), 3), item["file"], item["line"]))
    print(
        json.dumps(
            {"files_scanned": len(files), "findings_count": len(findings), "findings": findings},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
