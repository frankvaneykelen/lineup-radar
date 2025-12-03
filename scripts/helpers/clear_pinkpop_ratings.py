#!/usr/bin/env python3
"""
Clear ratings for Pinkpop 2026 so they can be re-enriched with the new 1-10 scale.
"""

import csv
from pathlib import Path

csv_path = Path("docs/pinkpop/2026/2026.csv")

# Read CSV
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Clear ratings
cleared_count = 0
for row in rows:
    if row.get('My rating', '').strip():
        row['My rating'] = ''
        cleared_count += 1

# Write back
with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✓ Cleared {cleared_count} ratings from Pinkpop 2026")
print(f"Now run: python enrich_artists.py --festival pinkpop --year 2026 --ai --parallel")
