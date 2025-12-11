#!/usr/bin/env python3
"""
Translate Dutch festival bios to English using Azure OpenAI.
"""

import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import csv
from festival_helpers import translate_text

def translate_bios(csv_file: str, festival: str):
    """Translate Festival Bio (NL) to Festival Bio (EN)."""
    
    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        artists = list(reader)
        headers = reader.fieldnames
    
    print(f"\n=== Translating Festival Bios for {festival} ===\n")
    print(f"Found {len(artists)} artists\n")
    
    updated_count = 0
    
    for idx, artist in enumerate(artists, 1):
        artist_name = artist.get('Artist', '')
        bio_nl = artist.get('Festival Bio (NL)', '').strip()
        bio_en = artist.get('Festival Bio (EN)', '').strip()
        
        # Skip if already has English bio or no Dutch bio
        if bio_en or not bio_nl:
            status = "✓ Already has EN bio" if bio_en else "○ No NL bio to translate"
            print(f"[{idx}/{len(artists)}] {artist_name}: {status}")
            continue
        
        print(f"[{idx}/{len(artists)}] {artist_name}: Translating...", flush=True)
        
        try:
            # Translate from Dutch to English
            translated = translate_text(bio_nl, from_lang="Dutch", to_lang="English")
            artist['Festival Bio (EN)'] = translated
            updated_count += 1
            print(f"  ✓ Translated ({len(translated)} chars)", flush=True)
        except Exception as e:
            print(f"  ⚠️  Translation failed: {e}", flush=True)
    
    # Write updated CSV
    if updated_count > 0:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(artists)
        
        print(f"\n✓ Translated {updated_count} bio(s)")
        print(f"  CSV updated: {csv_file}")
    else:
        print("\n○ No translations needed")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Translate festival bios from Dutch to English"
    )
    parser.add_argument(
        "--festival",
        type=str,
        required=True,
        help="Festival identifier (e.g., footprints)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    
    args = parser.parse_args()
    
    csv_file = f"festivals/{args.festival}/{args.year}/{args.year}.csv"
    
    if not Path(csv_file).exists():
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    
    translate_bios(csv_file, args.festival)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
