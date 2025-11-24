#!/usr/bin/env python3
"""
Validation script for AI enrichment

Re-runs AI enrichment on existing artists to check if the updated guidelines
would have prevented hallucinated data. Compares old vs new results.
"""

import csv
import sys
import re
import urllib.request
from pathlib import Path
from typing import Dict, List
import json
import os
import requests


def load_csv(csv_path: Path) -> tuple[List[str], List[Dict]]:
    """Load CSV file and return headers and rows."""
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def artist_name_to_slug(name: str) -> str:
    """Convert artist name to URL slug format."""
    import unicodedata
    
    # Handle special cases with direct mappings
    special_cases = {
        '¥ØU$UK€ ¥UK1MAT$U': 'yenouukeur-yenuk1matu',
        'Derya Yıldırım & Grup Şimşek': 'derya-yildirim-grup-simsek',
        'Florence + The Machine': 'florence-the-machine',
        'Arp Frique & The Perpetual Singers': 'arp-frique-the-perpetual-singers',
        'Mall Grab b2b Narciss': 'mall-grab-b2b-narciss',
        "Kin'Gongolo Kiniata": 'kingongolo-kiniata',
        'Lumï': 'lumi',
        'The xx': 'the-xx',
        'De Staat Becomes De Staat': 'de-staat-becomes-de-staat'
    }
    
    if name in special_cases:
        return special_cases[name]
    
    slug = name.lower()
    
    # Handle special replacements first
    slug = slug.replace(' + ', '-')
    slug = slug.replace('&', '-')
    slug = slug.replace(' b2b ', '-b2b-')
    
    # Normalize unicode characters (ï -> i, etc.)
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    return slug.strip('-')


def fetch_festival_bio(artist_name: str) -> str:
    """Fetch artist bio from festival website."""
    slug = artist_name_to_slug(artist_name)
    url = f"https://downtherabbithole.nl/programma/{slug}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # Extract Dutch bio from specific div class
        dutch_bio_pattern = r'<div[^>]*class="[^"]*column text-xl font-normal prose !max-w-none[^"]*"[^>]*>(.*?)</div>'
        dutch_bio_match = re.search(dutch_bio_pattern, html, re.DOTALL | re.IGNORECASE)
        festival_bio_nl = dutch_bio_match.group(1).strip() if dutch_bio_match else ""
        
        # Clean up HTML tags from bio but keep basic formatting
        festival_bio_nl = re.sub(r'<br\s*/?>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'<p[^>]*>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'</p>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'<[^>]+>', '', festival_bio_nl)
        festival_bio_nl = re.sub(r'\n\s*\n', '\n\n', festival_bio_nl).strip()
        
        # Try old pattern as fallback
        if not festival_bio_nl:
            bio_pattern = r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>'
            bio_match = re.search(bio_pattern, html, re.DOTALL | re.IGNORECASE)
            festival_bio = bio_match.group(1).strip() if bio_match else ""
            festival_bio = re.sub(r'<br\s*/?>', '\n', festival_bio)
            festival_bio = re.sub(r'<p[^>]*>', '\n', festival_bio)
            festival_bio = re.sub(r'</p>', '\n', festival_bio)
            festival_bio = re.sub(r'<[^>]+>', '', festival_bio)
            festival_bio_nl = re.sub(r'\n\s*\n', '\n\n', festival_bio).strip()
        
        return festival_bio_nl
    except Exception as e:
        print(f"  ⚠️  Could not fetch festival bio: {e}")
        return ""


def enrich_artist_with_ai(artist_name: str, festival_bio: str = "") -> Dict[str, str]:
    """
    Use Azure OpenAI to enrich artist data based on festival bio.
    
    Args:
        artist_name: Name of the artist
        festival_bio: Bio from festival website (if available)
    
    Returns:
        Dict with enriched artist data
    """
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    if not (azure_key and azure_endpoint):
        print(f"  ✗ {artist_name}: No Azure OpenAI credentials")
        return {}
    
    # Create prompt with festival bio context
    if festival_bio:
        prompt = f"""Based on this festival bio and your knowledge, provide information about "{artist_name}" in JSON format:

FESTIVAL BIO:
{festival_bio}

Return JSON with these exact fields:
{{
    "Genre": "primary genre(s), separated by /",
    "Country": "country of origin (use short names: UK, USA, DR Congo, etc.)",
    "Bio": "1-2 sentence background about the artist based on the festival bio and your knowledge",
    "My take": "brief critical assessment based on the festival bio and known reviews (1-2 sentences, or empty if insufficient info)",
    "My rating": "rating 1-10 based on critical acclaim and festival suitability (or empty if insufficient info)",
    "Spotify link": "full Spotify URL",
    "Number of People in Act": "number or empty",
    "Gender of Front Person": "Male/Female/Mixed/Non-binary",
    "Front Person of Color?": "Yes/No"
}}

CRITICAL: Generate Bio and My take primarily from the festival bio provided. Only leave empty if the festival bio provides no useful information. DO NOT hallucinate demographics - only answer if you know for certain. Use abbreviated country names: "UK" not "United Kingdom", "USA" not "United States", "DR Congo" not "Democratic Republic of the Congo"."""
    else:
        prompt = f"""Provide information about the musical artist "{artist_name}" in JSON format:

{{
    "Genre": "primary genre(s), separated by /",
    "Country": "country of origin (use short names: UK, USA, DR Congo, etc.)",
    "Bio": "1-2 sentence biography (or empty if insufficient info)",
    "My take": "brief critical assessment (1-2 sentences, or empty if insufficient info)",
    "My rating": "rating 1-10 (or empty if insufficient info)",
    "Spotify link": "full Spotify URL",
    "Number of People in Act": "number or empty",
    "Gender of Front Person": "Male/Female/Mixed/Non-binary",
    "Front Person of Color?": "Yes/No"
}}

CRITICAL: If you cannot find reliable information about this artist, leave Bio, My take, and My rating EMPTY. DO NOT hallucinate or guess. Use abbreviated country names: "UK" not "United Kingdom", "USA" not "United States", "DR Congo" not "Democratic Republic of the Congo"."""
    
    endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version=2024-12-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_key
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a music expert. Return only valid JSON. Never hallucinate data."},
            {"role": "user", "content": prompt}
        ],
        "model": azure_deployment,
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        # Extract JSON from response
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        artist_data = json.loads(content)
        return artist_data
        
    except Exception as e:
        print(f"  ✗ {artist_name}: API error - {e}")
        return {}


def validate_artist(artist_name: str, current_data: Dict, prompt_for_changes: bool = False) -> Dict:
    """
    Validate an artist by re-running AI enrichment with new guidelines.
    
    Args:
        artist_name: Name of the artist
        current_data: Current CSV data for the artist
        prompt_for_changes: If True, ask user whether to apply changes
    
    Returns:
        Dict with validation results including old vs new data comparison
    """
    print(f"\n🔍 Validating: {artist_name}")
    print(f"   Current data: Genre={current_data.get('Genre')}, Country={current_data.get('Country')}, Gender={current_data.get('Gender of Front Person')}")
    
    # Fetch festival bio first
    print(f"  → Fetching festival bio...")
    festival_bio = fetch_festival_bio(artist_name)
    if festival_bio:
        print(f"  ✓ Found festival bio ({len(festival_bio)} chars)")
    else:
        print(f"  ⚠️  No festival bio found")
    
    # Re-run enrichment with new guidelines and festival bio
    new_data = enrich_artist_with_ai(artist_name, festival_bio)
    
    if not new_data:
        print(f"   ⚠️  Could not get new enrichment data")
        return {
            'artist': artist_name,
            'status': 'error',
            'message': 'Failed to get AI response',
            'apply_changes': False
        }
    
    # Compare key fields
    changes = {}
    critical_fields = ['Genre', 'Country', 'Bio', 'Gender of Front Person', 'Front Person of Color?']
    
    for field in critical_fields:
        old_value = current_data.get(field, '').strip()
        new_value = new_data.get(field, '').strip()
        
        if old_value != new_value:
            changes[field] = {
                'old': old_value,
                'new': new_value
            }
    
    # Check if new data is more conservative (more empty fields)
    old_empty_count = sum(1 for f in critical_fields if not current_data.get(f, '').strip())
    new_empty_count = sum(1 for f in critical_fields if not new_data.get(f, '').strip())
    
    more_conservative = new_empty_count > old_empty_count
    
    apply_changes = False
    
    if changes:
        print(f"   ⚠️  DIFFERENCES FOUND:")
        for field, change in changes.items():
            print(f"      {field}:")
            print(f"         Old: {change['old'] or '(empty)'}")
            print(f"         New: {change['new'] or '(empty)'}")
        
        if more_conservative:
            print(f"   ✓ New guidelines are MORE conservative ({new_empty_count} empty fields vs {old_empty_count})")
        
        # Prompt user if requested
        if prompt_for_changes:
            response = input(f"\n   Apply these changes for {artist_name}? (Y/n): ").strip().lower()
            apply_changes = response != 'n' and response != 'no'
            if apply_changes:
                print(f"   ✓ Changes will be applied")
            else:
                print(f"   ✓ Changes skipped")
    else:
        print(f"   ✓ No differences found")
    
    return {
        'artist': artist_name,
        'status': 'validated',
        'changes': changes,
        'more_conservative': more_conservative,
        'old_empty_count': old_empty_count,
        'new_empty_count': new_empty_count,
        'apply_changes': apply_changes,
        'new_data': new_data if apply_changes else None
    }


def validate_csv(csv_path: Path, artists: List[str] = None, all_artists: bool = False):
    """
    Validate AI enrichment for specified artists or all artists.
    
    Args:
        csv_path: Path to CSV file
        artists: List of specific artist names to validate (optional)
        all_artists: If True, validate all artists in CSV
    """
    print(f"\n=== AI Enrichment Validation ===")
    print(f"Testing if new CRITICAL GUIDELINES prevent hallucinated data\n")
    
    headers, rows = load_csv(csv_path)
    
    results = []
    artists_to_validate = []
    
    if all_artists:
        artists_to_validate = [row for row in rows]
        print(f"Validating ALL {len(artists_to_validate)} artists...\n")
    elif artists:
        # Find specific artists
        for artist_name in artists:
            matching_rows = [row for row in rows if row.get('Artist', '').strip().lower() == artist_name.lower()]
            if matching_rows:
                artists_to_validate.extend(matching_rows)
            else:
                print(f"⚠️  Artist not found: {artist_name}")
    else:
        print("✗ No artists specified. Use --artist <name> or --all")
        return
    
    if not artists_to_validate:
        print("✗ No artists to validate")
        return
    
    # Validate each artist (prompting for changes after each one)
    for row in artists_to_validate:
        artist_name = row.get('Artist', '').strip()
        if not artist_name:
            continue
        
        result = validate_artist(artist_name, row, prompt_for_changes=True)
        results.append(result)
        
        # Apply changes immediately if user confirmed
        if result.get('apply_changes') and result.get('new_data'):
            for field, value in result['new_data'].items():
                if field in row:
                    row[field] = value
    
    # Summary
    print(f"\n\n=== VALIDATION SUMMARY ===\n")
    
    artists_with_changes = [r for r in results if r.get('changes')]
    changes_applied = sum(1 for r in results if r.get('apply_changes'))
    more_conservative_count = sum(1 for r in results if r.get('more_conservative'))
    
    print(f"Total validated: {len(results)}")
    print(f"Artists with differences: {len(artists_with_changes)}")
    print(f"Changes applied: {changes_applied}/{len(artists_with_changes)}")
    print(f"More conservative results: {more_conservative_count}/{len(results)}")
    
    if artists_with_changes:
        print(f"\n📋 Artists that had differences:\n")
        for result in artists_with_changes:
            status = "✓ Applied" if result.get('apply_changes') else "✗ Skipped"
            print(f"   {status}: {result['artist']}")
        
        print(f"\n💡 The new guidelines were:")
        if more_conservative_count > 0:
            print(f"   ✓ More conservative (left more fields empty) for {more_conservative_count} artist(s)")
        else:
            print(f"   ⚠️  Not necessarily more conservative - manual review recommended")
        
        # Save CSV if any changes were applied
        if changes_applied > 0:
            save_csv(csv_path, headers, rows)
            print(f"\n✓ Saved {changes_applied} change(s) to {csv_path}")
        else:
            print(f"\n✓ No changes applied - CSV remains unchanged")
    else:
        print(f"\n✓ No differences found - new guidelines produce same results")


def save_csv(csv_path: Path, headers: List[str], rows: List[Dict]):
    """Save CSV file with UTF-8 encoding."""
    import csv
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Main validation process."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate AI enrichment with new guidelines"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    parser.add_argument(
        "--artist",
        type=str,
        action="append",
        help="Specific artist name to validate (can be used multiple times)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all artists in CSV (⚠️  uses many API calls)"
    )
    
    args = parser.parse_args()
    
    # Check for API credentials
    import os
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not (azure_key and azure_endpoint):
        print("✗ Azure OpenAI credentials not found")
        print("\nSet environment variables:")
        print("  $env:AZURE_OPENAI_KEY = 'your-key'")
        print("  $env:AZURE_OPENAI_ENDPOINT = 'https://your-resource.cognitiveservices.azure.com'")
        print("  $env:AZURE_OPENAI_DEPLOYMENT = 'gpt-4o'")
        sys.exit(1)
    
    csv_path = Path(f"{args.year}.csv")
    
    validate_csv(csv_path, artists=args.artist, all_artists=args.all)


if __name__ == "__main__":
    main()
