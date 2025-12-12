"""
Migrate Website data from Social Links JSON to a separate Website column.
This standardizes the CSV structure across all festivals.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# Add parent directory to path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from festival_helpers import get_festival_config


def migrate_csv(csv_path):
    """Extract Website from Social Links and add as separate column."""
    print(f"\nProcessing: {csv_path}")
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    
    # Check if Website column already exists
    if 'Website' in fieldnames:
        print("  ✓ Website column already exists")
        # Check if we need to extract from Social Links
        changes = 0
        for row in rows:
            if not row.get('Website') and row.get('Social Links'):
                try:
                    social_links = json.loads(row['Social Links'])
                    if 'Website' in social_links:
                        row['Website'] = social_links['Website']
                        changes += 1
                except json.JSONDecodeError:
                    pass
        
        if changes > 0:
            print(f"  ✓ Extracted {changes} websites from Social Links")
            # Write back
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        return
    
    # Add Website column after Bio (or before Spotify if Bio doesn't exist)
    if 'Bio' in fieldnames:
        insert_index = fieldnames.index('Bio') + 1
    elif 'Spotify' in fieldnames:
        insert_index = fieldnames.index('Spotify')
    else:
        # Add at the end before Social Links
        if 'Social Links' in fieldnames:
            insert_index = fieldnames.index('Social Links')
        else:
            insert_index = len(fieldnames)
    
    fieldnames.insert(insert_index, 'Website')
    print(f"  → Adding Website column at position {insert_index}")
    
    # Extract website from Social Links
    extracted = 0
    for row in rows:
        row['Website'] = ''
        if row.get('Social Links'):
            try:
                social_links = json.loads(row['Social Links'])
                if 'Website' in social_links:
                    row['Website'] = social_links['Website']
                    extracted += 1
            except json.JSONDecodeError:
                pass
    
    if extracted > 0:
        print(f"  ✓ Extracted {extracted} websites from Social Links")
    
    # Write back
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  ✓ Migration complete")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Website column in festival CSVs'
    )
    parser.add_argument(
        '--festival',
        type=str,
        help='Festival slug (optional, processes all if not specified)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2026,
        help='Festival year (default: 2026)'
    )
    
    args = parser.parse_args()
    
    # Get list of festivals to process
    from festival_helpers.config import FESTIVALS
    
    if args.festival:
        festivals = [args.festival]
    else:
        festivals = list(FESTIVALS.keys())
    
    print(f"\n=== Migrating Website Column ===")
    print(f"Year: {args.year}")
    print(f"Festivals: {', '.join(festivals)}")
    
    for festival_slug in festivals:
        try:
            config = get_festival_config(festival_slug, args.year)
            csv_path = Path(config.output_dir) / f"{args.year}.csv"
            
            if not csv_path.exists():
                print(f"\n⚠️  Skipping {festival_slug}: CSV not found")
                continue
            
            migrate_csv(csv_path)
            
        except ValueError as e:
            print(f"\n⚠️  Skipping {festival_slug}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✓ Migration complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
