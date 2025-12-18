#!/usr/bin/env python3
"""Add Day, Start Time, End Time, Stage columns to festival CSVs."""

import csv
import sys
from pathlib import Path


def add_schedule_columns(csv_file):
    """Add schedule columns after Tagline column if they don't exist."""
    
    # Read the CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Check if columns already exist
    has_date = 'Date' in headers
    has_start = 'Start Time' in headers
    has_end = 'End Time' in headers
    has_stage = 'Stage' in headers
    has_day = 'Day' in headers  # Legacy column name
    
    if has_date and has_start and has_end and has_stage:
        print(f"✓ {csv_file.name} already has all schedule columns")
        return False
    
    # Create new headers list
    new_headers = []
    has_tagline = 'Tagline' in headers
    schedule_columns_added = False
    
    for header in headers:
        # Handle legacy Day -> Date rename
        if header == 'Day' and has_day and not has_date:
            new_headers.append('Date')
            print(f"  Renaming 'Day' to 'Date' in {csv_file.name}")
        else:
            new_headers.append(header)
        
        # After Tagline (or after Artist if no Tagline), add the schedule columns
        insertion_point = header == 'Tagline' or (header == 'Artist' and not has_tagline)
        if insertion_point and not schedule_columns_added:
            if not has_date and not has_day:
                new_headers.append('Date')
            if not has_start:
                new_headers.append('Start Time')
            if not has_end:
                new_headers.append('End Time')
            if not has_stage:
                new_headers.append('Stage')
            schedule_columns_added = True
    
    # Add empty values for new columns in all rows
    new_rows = []
    for row in rows:
        new_row = {}
        for header in new_headers:
            if header == 'Date' and has_day and 'Day' in row:
                # Copy Day value to Date
                new_row[header] = row['Day']
            elif header in row:
                new_row[header] = row[header]
            else:
                new_row[header] = ''
        new_rows.append(new_row)
    
    # Write back to CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_headers)
        writer.writeheader()
        writer.writerows(new_rows)
    
    print(f"✓ Updated {csv_file.name} with schedule columns")
    return True


def main():
    """Process all festival CSVs."""
    
    # Find all 2026 CSVs
    docs_path = Path(__file__).parent.parent.parent / 'docs'
    csv_files = list(docs_path.glob('**/2026/2026.csv'))
    
    if not csv_files:
        print("No CSV files found")
        return 1
    
    print(f"Found {len(csv_files)} festival CSVs\n")
    
    updated_count = 0
    for csv_file in sorted(csv_files):
        festival_name = csv_file.parent.parent.name
        print(f"Processing {festival_name}...")
        if add_schedule_columns(csv_file):
            updated_count += 1
        print()
    
    print(f"\nSummary: Updated {updated_count} of {len(csv_files)} CSVs")
    return 0


if __name__ == '__main__':
    sys.exit(main())
