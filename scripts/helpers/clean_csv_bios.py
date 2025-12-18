"""
Clean existing festival bio text in CSV files using GPT.

This script reads festival CSV files and cleans the Festival bio (NL) column
to fix whitespace issues from HTML scraping.

Usage:
    python scripts/helpers/clean_csv_bios.py --festival grauzone --year 2026
    python scripts/helpers/clean_csv_bios.py --all  # Clean all festivals
"""

import argparse
import csv
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.ai_client import clean_scraped_text
from helpers.config import FESTIVALS


def clean_festival_csv(festival_slug: str, year: int, dry_run: bool = False):
    """
    Clean bio text in a festival CSV file.
    
    Args:
        festival_slug: Festival slug (e.g., 'grauzone')
        year: Year (e.g., 2026)
        dry_run: If True, show changes without saving
    """
    csv_path = Path(f"docs/{festival_slug}/{year}/{year}.csv")
    
    if not csv_path.exists():
        print(f"  ❌ CSV not found: {csv_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Cleaning: {festival_slug} {year}")
    print(f"{'='*80}\n")
    
    # Read CSV
    rows = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Track changes
    changes = 0
    
    # Process each row
    for i, row in enumerate(rows, 1):
        artist_name = row.get('Artist', 'Unknown')
        
        # Columns that might contain scraped bio text
        bio_columns = ['Bio', 'Festival bio (NL)', 'Festival Bio (EN)']
        row_changed = False
        
        for col in bio_columns:
            bio_text = row.get(col, '')
            
            if not bio_text or not bio_text.strip():
                continue
            
            # Clean the bio
            cleaned_bio = clean_scraped_text(bio_text)
            
            # Check if changed
            if cleaned_bio != bio_text:
                if not row_changed:
                    changes += 1
                    print(f"[{i}/{len(rows)}] {artist_name}")
                    row_changed = True
                
                print(f"  Column: {col}")
                print(f"    BEFORE: {bio_text[:80]}...")
                print(f"    AFTER:  {cleaned_bio[:80]}...")
                
                if not dry_run:
                    row[col] = cleaned_bio
        
        if row_changed:
            print()
    
    # Save if changes were made and not dry run
    if changes > 0:
        if dry_run:
            print(f"✓ Found {changes} bio(s) to clean (dry run - no changes saved)")
        else:
            # Write back to CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✓ Cleaned {changes} bio(s) and saved to {csv_path}")
    else:
        print(f"✓ No issues found - all bios are clean!")


def main():
    parser = argparse.ArgumentParser(description='Clean scraped bio text in festival CSV files')
    parser.add_argument('--festival', help='Festival slug (e.g., grauzone)')
    parser.add_argument('--year', type=int, help='Year (e.g., 2026)')
    parser.add_argument('--all', action='store_true', help='Clean all festival CSV files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    
    args = parser.parse_args()
    
    if args.all:
        # Clean all festivals
        for festival_slug in FESTIVALS.keys():
            for year_dir in Path(f"docs/{festival_slug}").glob("*"):
                if year_dir.is_dir() and year_dir.name.isdigit():
                    year = int(year_dir.name)
                    clean_festival_csv(festival_slug, year, args.dry_run)
    elif args.festival and args.year:
        clean_festival_csv(args.festival, args.year, args.dry_run)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/helpers/clean_csv_bios.py --festival grauzone --year 2026")
        print("  python scripts/helpers/clean_csv_bios.py --festival grauzone --year 2026 --dry-run")
        print("  python scripts/helpers/clean_csv_bios.py --all")
        sys.exit(1)


if __name__ == '__main__':
    main()
