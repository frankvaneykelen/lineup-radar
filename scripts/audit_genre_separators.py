#!/usr/bin/env python3
"""Audit and optionally fix genre separator consistency across festival CSV files."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from helpers.genre_utils import normalize_genre_value


def find_csv_files(root: Path) -> List[Path]:
    """Return CSV files under docs/ that look like lineup data."""
    return sorted(path for path in root.rglob("*.csv") if path.is_file())


def load_csv(csv_path: Path) -> tuple[List[str], List[Dict[str, str]]]:
    """Load CSV rows from disk."""
    with open(csv_path, "r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    return headers, rows


def save_csv(csv_path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    """Write CSV rows back to disk."""
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def audit_csv(csv_path: Path, fix: bool = False) -> List[Dict[str, str]]:
    """Find comma-separated genre values in one CSV file.

    Returns a list of offending rows with file, artist, original genre, and normalized genre.
    """
    headers, rows = load_csv(csv_path)
    if "Genre" not in headers or "Artist" not in headers:
        return []

    offenders: List[Dict[str, str]] = []
    changed = False

    for row in rows:
        genre = (row.get("Genre") or "").strip()
        if not genre or "," not in genre:
            continue

        normalized = normalize_genre_value(genre)
        offenders.append(
            {
                "file": str(csv_path),
                "artist": (row.get("Artist") or "").strip(),
                "genre": genre,
                "normalized": normalized,
            }
        )

        if fix and normalized != genre:
            row["Genre"] = normalized
            changed = True

    if fix and changed:
        save_csv(csv_path, headers, rows)

    return offenders


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Audit festival CSV files for comma-separated genre values."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("docs"),
        help="Directory to scan for CSV files (default: docs)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Normalize comma-separated genre values to slash-separated values in place.",
    )
    parser.add_argument(
        "--fail-on-find",
        action="store_true",
        help="Exit with status 1 if any comma-separated genre values are found.",
    )
    return parser


def main() -> int:
    """Run the audit."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.root.exists():
        print(f"✗ Scan root not found: {args.root}")
        return 2

    csv_files = find_csv_files(args.root)
    if not csv_files:
        print(f"✗ No CSV files found under {args.root}")
        return 2

    total_offenders: List[Dict[str, str]] = []
    for csv_path in csv_files:
        total_offenders.extend(audit_csv(csv_path, fix=args.fix))

    action = "fixed" if args.fix else "found"
    if not total_offenders:
        print(f"✓ No comma-separated genre values {action} under {args.root}")
        return 0

    print(f"⚠ Found {len(total_offenders)} comma-separated genre value(s) across festival CSV files:\n")
    for offender in total_offenders:
        print(f"- {offender['file']}")
        print(f"  Artist: {offender['artist']}")
        print(f"  Genre: {offender['genre']}")
        print(f"  Normalized: {offender['normalized']}")

    if args.fix:
        print("\n✓ Offending values were normalized in place.")

    return 1 if args.fail_on_find else 0


if __name__ == "__main__":
    raise SystemExit(main())