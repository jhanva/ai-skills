#!/usr/bin/env python3
"""Enlaza skills del repo en el scope personal sin duplicar su contenido."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class LinkItem:
    name: str
    source: Path
    destination: Path


def available_plugins(repo: Path) -> list[str]:
    return sorted(
        path.name
        for path in (repo / "plugins").iterdir()
        if path.is_dir() and (path / "skills").is_dir()
    )


def build_plan(repo: Path, target: Path, plugins: list[str]) -> list[LinkItem]:
    known = set(available_plugins(repo))
    unknown = sorted(set(plugins) - known)
    if unknown:
        raise ValueError(f"Plugins desconocidos: {', '.join(unknown)}")

    plan: list[LinkItem] = []
    seen: set[str] = set()
    for plugin in plugins:
        for source in sorted((repo / "plugins" / plugin / "skills").iterdir()):
            if not source.is_dir() or not (source / "SKILL.md").is_file():
                continue
            if source.name in seen:
                raise ValueError(f"Skill duplicada entre plugins: {source.name}")
            seen.add(source.name)
            plan.append(LinkItem(source.name, source.resolve(), target / source.name))
    return plan


def is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name != "nt" or not path.exists():
        return False
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def same_link(destination: Path, source: Path) -> bool:
    return is_link_like(destination) and destination.resolve(strict=False) == source.resolve()


def create_link(item: LinkItem, junction: bool) -> None:
    if junction:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(item.destination), str(item.source)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise OSError(result.stderr.strip() or result.stdout.strip())
        return
    item.destination.symlink_to(item.source, target_is_directory=True)


def apply_links(plan: list[LinkItem], dry_run: bool, junction: bool = False) -> list[str]:
    errors: list[str] = []
    for item in plan:
        if same_link(item.destination, item.source):
            print(f"OK      {item.name} -> {item.source}")
            continue
        if item.destination.exists() or item.destination.is_symlink():
            errors.append(f"COLISION {item.destination}: ya existe y no apunta a {item.source}")
            continue
        if dry_run:
            action = "JUNCTION" if junction else "LINK"
            print(f"{action:8} {item.name} -> {item.source}")
            continue
        item.destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            create_link(item, junction)
            action = "JUNCTION" if junction else "LINK"
            print(f"{action:8} {item.name} -> {item.source}")
        except OSError as exc:
            if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                errors.append(
                    f"PERMISO {item.destination}: activa Windows Developer Mode "
                    "o ejecuta una terminal elevada"
                )
            else:
                errors.append(f"ERROR   {item.destination}: {exc}")
    return errors


def remove_links(plan: list[LinkItem], dry_run: bool) -> list[str]:
    errors: list[str] = []
    for item in plan:
        if not item.destination.exists() and not item.destination.is_symlink():
            continue
        if not same_link(item.destination, item.source):
            errors.append(f"OMITIR  {item.destination}: no es un enlace gestionado por este repo")
            continue
        print(f"REMOVE  {item.name} -> {item.source}")
        if not dry_run:
            if item.destination.is_symlink():
                item.destination.unlink()
            else:
                os.rmdir(item.destination)
    return errors


def show_status(plan: list[LinkItem]) -> list[str]:
    errors: list[str] = []
    for item in plan:
        if same_link(item.destination, item.source):
            state = "linked"
        elif item.destination.exists() or item.destination.is_symlink():
            state = "collision"
            errors.append(str(item.destination))
        else:
            state = "missing"
        print(f"{state:9} {item.name} -> {item.source}")
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expone skills del repo en ~/.agents/skills mediante symlinks."
    )
    parser.add_argument("--plugin", action="append", dest="plugins")
    parser.add_argument("--all", action="store_true", help="Incluye todos los plugins")
    parser.add_argument("--target", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument(
        "--junction",
        action="store_true",
        help="En Windows crea junctions vivas cuando los symlinks requieren privilegios",
    )
    args = parser.parse_args(argv)
    if args.all and args.plugins:
        parser.error("usa --all o --plugin, no ambos")
    if args.status and args.remove:
        parser.error("usa --status o --remove, no ambos")
    if args.junction and os.name != "nt":
        parser.error("--junction solo esta disponible en Windows")
    if not args.all and not args.plugins:
        args.plugins = ["core"]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    plugins = available_plugins(ROOT) if args.all else args.plugins
    try:
        plan = build_plan(ROOT, args.target.expanduser(), plugins)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.status:
        errors = show_status(plan)
    elif args.remove:
        errors = remove_links(plan, args.dry_run)
    else:
        errors = apply_links(plan, args.dry_run, junction=args.junction)

    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
