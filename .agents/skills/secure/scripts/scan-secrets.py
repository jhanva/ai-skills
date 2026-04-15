#!/usr/bin/env python3
"""
scan-secrets.py — Escanea archivos en busca de secrets expuestos.

Uso:
  python3 scan-secrets.py TARGET_DIR                    # Escanea todo el directorio
  git diff --name-only HEAD | python3 scan-secrets.py --stdin TARGET_DIR  # Solo archivos del stdin

Output: JSON a stdout con hallazgos.
Exit codes: 0 = limpio, 1 = hallazgos encontrados, 2 = error
"""

import json
import os
import re
import sys
from pathlib import Path

PATTERNS = [
    # Alta confianza
    ("AWS Access Key", r"AKIA[0-9A-Z]{16}", "high"),
    ("AWS Secret Key", r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}", "high"),
    ("GitHub Token (classic)", r"ghp_[A-Za-z0-9]{36}", "high"),
    ("GitHub Token (fine-grained)", r"github_pat_[A-Za-z0-9_]{82}", "high"),
    ("GitHub OAuth Token", r"gho_[A-Za-z0-9]{36}", "high"),
    ("GitLab Token", r"glpat-[A-Za-z0-9\-]{20}", "high"),
    ("Slack Bot Token", r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}", "high"),
    ("Slack Webhook", r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}", "high"),
    ("Stripe Secret Key", r"sk_live_[A-Za-z0-9]{24,}", "high"),
    ("Stripe Publishable Key", r"pk_live_[A-Za-z0-9]{24,}", "high"),
    ("SendGrid API Key", r"SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}", "high"),
    ("Google API Key", r"AIza[0-9A-Za-z\-_]{35}", "high"),
    ("npm Token", r"npm_[A-Za-z0-9]{36}", "high"),
    ("PyPI Token", r"pypi-[A-Za-z0-9]{50,}", "high"),
    ("Twilio API Key", r"SK[0-9a-fA-F]{32}", "high"),
    # Confianza media
    ("Private Key", r"-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----", "medium"),
    ("Generic Password", r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{8,}["\']', "medium"),
    ("Generic Secret", r'(?i)(secret|api_key|apikey|access_key)\s*[:=]\s*["\'][^"\']{8,}["\']', "medium"),
    ("Connection String", r"(?i)(mongodb|postgres|mysql|redis)://[^:]+:[^@]+@", "medium"),
    ("JWT Hardcoded", r"eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", "medium"),
]

IGNORE_DIRS = {
    "node_modules", ".git", "vendor", "__pycache__", "dist", "build",
    ".next", "target", ".venv", "venv", "env", ".tox", "coverage",
}

IGNORE_EXTENSIONS = {
    ".lock", ".min.js", ".min.css", ".map", ".woff", ".woff2", ".ttf",
    ".eot", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp3", ".mp4", ".pdf", ".zip", ".tar", ".gz", ".jar", ".class",
}

IGNORE_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
    "Pipfile.lock", "poetry.lock", "composer.lock", "go.sum",
}

IGNORE_PATTERNS_IN_PATH = {"test", "spec", "fixture", "mock", "fake", "example", "sample", "template"}


def should_scan(filepath: Path) -> bool:
    parts = filepath.parts
    if any(d in IGNORE_DIRS for d in parts):
        return False
    if filepath.suffix.lower() in IGNORE_EXTENSIONS:
        return False
    if filepath.name in IGNORE_FILENAMES:
        return False
    # Skip test files for medium-confidence patterns (handled in scan)
    return True


def is_test_file(filepath: Path) -> bool:
    name = filepath.name.lower()
    path_str = str(filepath).lower()
    return (
        any(p in path_str for p in IGNORE_PATTERNS_IN_PATH)
        or name.endswith((".test.js", ".test.ts", ".spec.js", ".spec.ts",
                          "_test.py", "_test.go", ".test.jsx", ".test.tsx"))
        or name.startswith("test_")
        or name in (".env.example", ".env.sample", ".env.template")
    )


def scan_file(filepath: Path) -> list:
    findings = []
    try:
        content = filepath.read_text(errors="ignore")
    except (PermissionError, OSError):
        return findings

    lines = content.splitlines()
    test_file = is_test_file(filepath)

    for line_num, line in enumerate(lines, 1):
        if len(line) > 2000:  # skip minified lines
            continue
        for name, pattern, confidence in PATTERNS:
            # Skip medium-confidence in test files
            if confidence == "medium" and test_file:
                continue
            if re.search(pattern, line):
                findings.append({
                    "file": str(filepath),
                    "line": line_num,
                    "type": name,
                    "confidence": confidence,
                    "content": line.strip()[:120],  # truncate for safety
                })
    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage: scan-secrets.py [--stdin] TARGET_DIR", file=sys.stderr)
        sys.exit(2)

    use_stdin = "--stdin" in sys.argv
    target_dir = Path(sys.argv[-1]).resolve()

    if not target_dir.is_dir():
        print(f"Error: {target_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    if use_stdin:
        # Read file list from stdin
        files = []
        for line in sys.stdin:
            fp = target_dir / line.strip()
            if fp.is_file() and should_scan(fp):
                files.append(fp)
    else:
        # Scan all files
        files = [f for f in target_dir.rglob("*") if f.is_file() and should_scan(f)]

    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f))

    # Make paths relative to target
    for finding in all_findings:
        try:
            finding["file"] = str(Path(finding["file"]).relative_to(target_dir))
        except ValueError:
            pass

    output = {
        "target": str(target_dir),
        "files_scanned": len(files),
        "findings_count": len(all_findings),
        "findings": sorted(all_findings, key=lambda x: (
            0 if x["confidence"] == "high" else 1,
            x["file"],
            x["line"],
        )),
    }

    json.dump(output, sys.stdout, indent=2)
    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
