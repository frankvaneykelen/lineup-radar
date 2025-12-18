#!/usr/bin/env python3
"""
Add Tagline column to festival CSVs that don't have it yet.
"""

import sys
from pathlib import Path
import csv

sys.path.insert(0, str(Path(__file__).parent.parent))


def add_tagline_column(csv_path: Path):
    """Add Tagline column after Artist if it doesn't exist."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        rows = list(reader)
    
    # Check if Tagline column exists
    if "Tagline" in headers:
        return False
    
    # Find Artist column position
    if "Artist" not in headers:
        print(f"  ⚠️  No Artist column found in {csv_path}")
        return False
    
    artist_index = headers.index("Artist")
    
    # Insert Tagline after Artist
    headers.insert(artist_index + 1, "Tagline")
    
    # Add empty Tagline field to all rows
    for row in rows:
        row["Tagline"] = ""
    
    # Save CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    return True


def main():
    """Add Tagline column to all festival CSVs."""
    docs_path = Path(__file__).parent.parent.parent / "docs"
    
    print("=== Adding Tagline Column ===\n")
    
    updated_count = 0
    
    # Find all festival directories
    festival_dirs = [d for d in docs_path.iterdir() 
                     if d.is_dir() and not d.name.startswith('.') and d.name != 'shared']
    
    for festival_dir in sorted(festival_dirs):
        year_dir = festival_dir / "2026"
        csv_path = year_dir / "2026.csv"
        
        if csv_path.exists():
            festival_name = festival_dir.name
            if add_tagline_column(csv_path):
                print(f"✓ Added Tagline column to {festival_name}")
                updated_count += 1
            else:
                print(f"  {festival_name} already has Tagline column")
    
    print(f"\n✅ Complete! Updated {updated_count} festival(s).")


if __name__ == "__main__":
    main()
