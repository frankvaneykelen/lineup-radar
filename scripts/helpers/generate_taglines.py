#!/usr/bin/env python3
"""
Generate taglines for all artists across all festivals.

This script generates catchy taglines for artists that don't have one yet.
It processes all festivals and updates the Tagline column in the CSV files.
"""

import sys
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import csv
import json
import os
import requests
from typing import Dict, List


def load_csv(csv_path: Path) -> tuple[List[str], List[Dict]]:
    """Load CSV file and return headers and rows."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def save_csv(csv_path: Path, headers: List[str], rows: List[Dict]):
    """Save CSV file with UTF-8 encoding."""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def generate_tagline(artist_name: str, bio: str = "", genre: str = "", ai_summary: str = "") -> str:
    """
    Generate a catchy tagline for an artist using AI.
    
    Args:
        artist_name: Name of the artist
        bio: Artist bio
        genre: Artist genre
        ai_summary: AI-generated summary
    
    Returns:
        Tagline string (3-7 words) or empty string if insufficient info
    """
    # CRITICAL: Do not hallucinate taglines when there's no information
    # Skip if we don't have at least one of: bio, genre, or AI summary
    if not bio and not genre and not ai_summary:
        return ""
    
    context_info = []
    if bio:
        context_info.append(f"Bio: {bio}")
    if genre:
        context_info.append(f"Genre: {genre}")
    if ai_summary:
        context_info.append(f"Summary: {ai_summary}")
    
    context = "\n".join(context_info) if context_info else "No additional information available."
    
    prompt = f"""Generate a catchy, punchy tagline (3-7 words) for the musical artist "{artist_name}".

Context:
{context}

TAGLINE GUIDELINES:
- 3-7 words maximum
- Capture the essence or uniqueness of the artist
- Be creative, descriptive, and memorable
- Can be dramatic, poetic, or straightforward
- Focus on their sound, reputation, or significance

EXAMPLES of good taglines:
- "The most famous animated band on earth" (Gorillaz)
- "Rock music's chief anti-hero" (Jack White)
- "Legendary songsmith of darkness and devotion" (Nick Cave)
- "Captivating Mediterranean dream pop" (∑tella)
- "Modern soul man with deep bag" (Curtis Harding)
- "The queen of Southern gothic folk pop" (Ethel Cain)
- "Chameleon-like alt folk siren" (Aldous Harding)
- "Warm-blooded & ethereal electronic pop" (Ão)
- "One of death metal's most visionary bands" (Blood Incantation)

Return ONLY the tagline text, no quotes, no JSON, no additional commentary."""

    # Check for Azure OpenAI
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    if not azure_key or not azure_endpoint:
        print(f"  ✗ {artist_name}: No Azure OpenAI credentials found")
        return ""
    
    endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version=2024-12-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_key
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a creative music journalist who writes catchy, memorable taglines. Be concise and impactful."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": azure_deployment,
        "temperature": 0.8,  # Higher temperature for more creative taglines
        "max_tokens": 50
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        tagline = result["choices"][0]["message"]["content"].strip()
        
        # Remove quotes if AI added them
        tagline = tagline.strip('"').strip("'")
        
        return tagline
        
    except Exception as e:
        print(f"  ✗ {artist_name}: Error generating tagline - {e}")
        return ""


def process_festival(festival_path: Path, year: int = 2026):
    """Process a single festival CSV to generate missing taglines."""
    csv_path = festival_path / f"{year}.csv"
    
    if not csv_path.exists():
        return 0
    
    festival_name = festival_path.parent.name
    print(f"\n📁 Processing {festival_name} {year}...")
    
    headers, rows = load_csv(csv_path)
    
    # Check if Tagline column exists
    if "Tagline" not in headers:
        print(f"  ⚠️  No Tagline column found - skipping")
        return 0
    
    updated_count = 0
    
    for row in rows:
        artist_name = row.get("Artist", "").strip()
        if not artist_name:
            continue
        
        # Skip if tagline already exists
        if row.get("Tagline", "").strip():
            continue
        
        # Get artist information
        bio = row.get("Bio", "").strip()
        genre = row.get("Genre", "").strip()
        ai_summary = row.get("AI Summary", "").strip()
        
        # Skip if no information available (prevent hallucination)
        if not bio and not genre and not ai_summary:
            print(f"  ⊘ {artist_name}: Skipped (no bio/genre/summary - cannot generate tagline without info)")
            continue
        
        # Generate tagline
        tagline = generate_tagline(artist_name, bio, genre, ai_summary)
        
        if tagline:
            row["Tagline"] = tagline
            updated_count += 1
            print(f"  ✓ {artist_name}: \"{tagline}\"")
        else:
            print(f"  ⚠️  {artist_name}: Failed to generate tagline")
    
    if updated_count > 0:
        save_csv(csv_path, headers, rows)
        print(f"  💾 Saved {updated_count} taglines")
    
    return updated_count


def main():
    """Main function to process all festivals."""
    parser = argparse.ArgumentParser(
        description='Generate taglines for artists that don\'t have one yet'
    )
    parser.add_argument(
        '--festival',
        type=str,
        help='Festival slug (e.g., alkmaarse-eigenste)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2026,
        help='Festival year (default: 2026)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all festivals'
    )
    
    args = parser.parse_args()
    
    docs_path = Path(__file__).parent.parent.parent / "docs"
    
    if args.festival:
        # Process single festival
        festival_dir = docs_path / args.festival / str(args.year)
        
        if not festival_dir.exists():
            print(f"✗ Festival directory not found: {festival_dir}")
            sys.exit(1)
        
        print(f"=== Generating Taglines for {args.festival} {args.year} ===")
        print("\nThis will generate taglines for artists that don't have one yet.")
        print("Existing taglines will be preserved.\n")
        
        count = process_festival(festival_dir, args.year)
        
        if count > 0:
            print(f"\n✅ Complete! Generated {count} taglines.")
            print("\n💡 Tip: Review the generated taglines and adjust if needed.")
            print(f"   Then regenerate HTML with: .\\scripts\\regenerate_festival.ps1 -Festival {args.festival} -Year {args.year}")
        else:
            print("\n✅ No taglines needed to be generated.")
    
    elif args.all:
        # Process all festivals
        print("=== Generating Taglines for All Festivals ===")
        print("\nThis will generate taglines for artists that don't have one yet.")
        print("Existing taglines will be preserved.\n")
        
        total_updated = 0
        
        # Find all festival directories
        festival_dirs = [d for d in docs_path.iterdir() 
                         if d.is_dir() and not d.name.startswith('.') and d.name != 'shared']
        
        for festival_dir in sorted(festival_dirs):
            year_dir = festival_dir / str(args.year)
            if year_dir.exists():
                count = process_festival(year_dir, args.year)
                total_updated += count
        
        print(f"\n✅ Complete! Generated {total_updated} taglines across all festivals.")
        
        if total_updated > 0:
            print("\n💡 Tip: Review the generated taglines and adjust if needed.")
            print("   Then regenerate HTML with: .\\scripts\\regenerate_all.ps1")
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/helpers/generate_taglines.py --festival alkmaarse-eigenste --year 2026")
        print("  python scripts/helpers/generate_taglines.py --all")
        print("  python scripts/helpers/generate_taglines.py --all --year 2025")


if __name__ == "__main__":
    main()
