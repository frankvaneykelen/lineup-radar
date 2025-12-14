#!/usr/bin/env python3
"""
AI-powered artist data enrichment for Down The Rabbit Hole Festival Tracker

Uses AI to automatically fill in artist details (genre, country, bio, etc.)
when new artists are added to the CSV.
"""

import sys
from pathlib import Path

# Add scripts directory to sys.path to import helpers
sys.path.insert(0, str(Path(__file__).parent))

import csv
from typing import Dict, List
import json
from helpers.config import get_festival_config


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


def save_csv(csv_path: Path, headers: List[str], rows: List[Dict]):
    """Save CSV file with UTF-8 encoding."""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def needs_enrichment(row: Dict, force: bool = False) -> bool:
    """Check if artist row needs data enrichment."""
    if force:
        return True  # Enrich all fields regardless of current values
    essential_fields = ["Genre", "Country", "Bio", "AI Summary", "AI Rating"]
    return any(not row.get(field, "").strip() for field in essential_fields)


def create_enrichment_prompt(artist_name: str, existing_bio: str = "") -> str:
    """Create a prompt for AI to enrich artist data."""
    bio_instruction = ""
    context_note = ""
    
    if existing_bio:
        bio_instruction = f'\n    "Bio": "{existing_bio}" (PRESERVE THIS EXACT BIO - do not change or rewrite it),'
        context_note = f"\n\nCONTEXT: The artist's bio is: \"{existing_bio}\"\nUse this bio as the primary source of truth. Base your critical assessment on the information in this bio, not on speculation or generic statements."
    else:
        bio_instruction = '\n    "Bio": "concise 1-2 sentence biography focusing on their music style and achievements",'
    
    return f"""Provide comprehensive information about the musical artist "{artist_name}" in JSON format with these exact fields:{context_note}

{{
    "Genre": "primary genre(s), separated by /",
    "Country": "country of origin (use short names: UK, USA, DR Congo, etc.)",{bio_instruction}
    "AI Summary": "brief critical assessment based on the bio provided or from reviews/consensus - BE SPECIFIC about their sound/style, avoid generic phrases like 'emerging artist' or 'shows promise' (or empty string if no bio and insufficient public info)",
    "AI Rating": "rating from 1-10 based on critical acclaim, live reputation, and artistic significance (or empty string if insufficient info)",
    "Spotify link": "full Spotify artist URL (https://open.spotify.com/artist/...)",
    "Number of People in Act": "number as integer, or empty if solo/varies",
    "Gender of Front Person": "Male/Female/Mixed/Non-binary",
    "Front Person of Color?": "Yes/No"
}}

CRITICAL GUIDELINES:
- If a bio is provided in the context, use it as your PRIMARY source - extract genre, country, and style details from it
- For "AI Summary": If bio is provided, write a specific assessment based on the bio's content (their sound, influences, achievements mentioned)
- AVOID generic phrases like "emerging artist with growing following" or "shows promise" - be specific about their musical style
- Example good "AI Summary": "Their blend of Anatolian psychedelia with modern electronic beats creates a hypnotic sound; strong stage presence"
- Example bad "AI Summary": "Emerging artist with a growing following, performances show promise"
- Provide information for ALL artists unless they are completely unknown (no online presence whatsoever)
- For artists with bio: extract concrete details about their sound, not vague assessments
- For artists without bio: provide genre, country, basic info, but be honest if you lack details (leave AI Summary/rating empty)
- AI Rating: VALUE innovation, freshness, and emerging talent - new artists with unique sound or buzz deserve 7-9, not 4-5
- DISCOVERY FOCUS: Treat being "new" or "emerging" as a POSITIVE attribute, not a limitation
- Only leave fields COMPLETELY empty if the artist has zero online presence (very rare for festival acts)

RATING SCALE (USE THE FULL RANGE - weighted for discoverability):
- 10: Reserved ONLY for universally acclaimed legends (e.g., Radiohead, Beyoncé, Kendrick Lamar level)
- 8-9: Exceptional artists - includes both established acts with strong track record AND exciting emerging artists with innovative sound, strong buzz, or unique artistic vision
- 6-7: Quality artists - solid established acts OR promising new artists with good reviews and interesting musical approach
- 4-5: Developing artists with potential OR established acts with mixed/declining reception
- 1-3: Very limited appeal, poor reviews, or completely unknown
- IMPORTANT: For discovery purposes, FAVOR innovation, freshness, and emerging talent alongside critical acclaim
- NEW/EMERGING artists with buzz, unique sound, or critical excitement should rate 7-9 (not 4-5)
- ESTABLISHED artists should be rated based on their current relevance and live reputation, not just past achievements
- Don't penalize artists for being new - youth, innovation, and freshness are POSITIVE factors
- Artists who are "ones to watch" or have "breakout potential" deserve higher ratings (7-8 range)
- Use official Spotify URLs only
- For groups with multiple frontpeople, use "Mixed" for gender
- Be accurate about demographics; use "Yes" for Front Person of Color only if confirmed, otherwise "No"
- Leave "Number of People in Act" empty for solo artists or when it varies (DJs, producers)
- Use abbreviated country names: "UK" not "United Kingdom", "USA" not "United States", "DR Congo" not "Democratic Republic of the Congo"
- When in doubt about ANY field, leave it empty rather than guessing

Return ONLY valid JSON, no additional text."""


def enrich_artist_with_ai(artist_name: str, existing_bio: str = "", rating_boost: float = 0.0) -> Dict[str, str]:
    """
    Use Azure OpenAI or GitHub Models API to enrich artist data.
    
    Args:
        artist_name: Name of the artist to enrich
        existing_bio: Existing bio to preserve (if any)
        rating_boost: Rating adjustment for discovery/curated festivals (default 0.0)
    
    Priority order:
    1. Azure OpenAI (if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT are set)
    2. GitHub Models (if GITHUB_TOKEN is set)
    3. OpenAI (if OPENAI_API_KEY is set)
    """
    import os
    import requests
    import subprocess
    import time
    
    # Check for Azure OpenAI first (recommended for pay-as-you-go)
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # Default to gpt-4o-mini (less conservative, much cheaper) or set AZURE_OPENAI_DEPLOYMENT to override
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    if azure_key and azure_endpoint:
        # Use Azure OpenAI
        endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version=2024-12-01-preview"
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_key
        }
        model_name = azure_deployment
        use_azure = True
    else:
        # Try GitHub token
        api_key = None
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                api_key = result.stdout.strip()
        except:
            pass
        
        if not api_key:
            api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print(f"  ✗ {artist_name}: No authentication found")
            print(f"     Option 1 (Recommended): Azure OpenAI with your credits:")
            print(f"       Set: $env:AZURE_OPENAI_KEY = 'your-key'")
            print(f"            $env:AZURE_OPENAI_ENDPOINT = 'https://your-resource.openai.azure.com'")
            print(f"     Option 2: GitHub Models (free, rate limited):")
            print(f"       Set: $env:GITHUB_TOKEN = 'your-token'")
            return {}
        
        endpoint = "https://models.github.ai/inference/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        model_name = "openai/gpt-4o"
        use_azure = False
    
    prompt = create_enrichment_prompt(artist_name, existing_bio)
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a music expert providing accurate, factual information about artists. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model_name,
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON from response
        content = content.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        artist_data = json.loads(content)
        provider = "Azure OpenAI" if use_azure else "GitHub Models"
        
        # Validate and log rating issues
        rating = artist_data.get("AI Rating", "")
        my_take = artist_data.get("AI Summary", "")
        
        # Convert rating to string and handle edge cases
        if rating == 0 or rating == "0":
            print(f"  ⚠️  {artist_name}: AI returned rating 0 (not enough publicly available critical reviews or performance data) - setting to empty")
            artist_data["AI Rating"] = ""
        elif not str(rating).strip():
            print(f"  ⚠️  {artist_name}: AI returned empty rating (not enough publicly available critical reviews or performance data)")
            artist_data["AI Rating"] = ""
        else:
            # Apply rating boost for discovery/curated festivals
            if rating_boost != 0.0:
                try:
                    original_rating = float(rating)
                    boosted_rating = original_rating + rating_boost
                    # Clamp to 1-10 range and round to nearest integer
                    boosted_rating = max(1, min(10, round(boosted_rating)))
                    artist_data["AI Rating"] = str(boosted_rating)
                    if boosted_rating != original_rating:
                        print(f"  📊 {artist_name}: Rating adjusted {original_rating:.1f} → {boosted_rating} (boost: +{rating_boost})")
                except (ValueError, TypeError):
                    # Keep original rating if conversion fails
                    pass
        
        if not my_take.strip():
            print(f"  ⚠️  {artist_name}: AI returned empty 'AI Summary' (not enough publicly available critical reviews or performance data)")
        
        print(f"  ✓ {artist_name}: Enriched with AI ({provider})")
        
        # No delay needed with Azure OpenAI
        return artist_data
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if "429" in error_msg:
            # Try to get rate limit info from response headers
            if hasattr(e, 'response') and e.response is not None:
                headers = e.response.headers
                retry_after = headers.get('Retry-After', '60')
                try:
                    wait_seconds = int(retry_after)
                    wait_minutes = wait_seconds / 60
                    if wait_seconds > 300:  # More than 5 minutes
                        print(f"  ⚠️  {artist_name}: Rate limited - need to wait {wait_minutes:.1f} minutes")
                        print(f"     GitHub Models free tier has limited requests.")
                        print(f"     Skipping for now - run the script again later to continue.")
                        return {}
                    else:
                        print(f"  ⚠️  {artist_name}: Rate limited, waiting {wait_seconds} seconds...")
                        time.sleep(wait_seconds)
                        return {}
                except:
                    wait_seconds = 60
            else:
                wait_seconds = 60
            print(f"  ⚠️  {artist_name}: Rate limited, waiting {wait_seconds} seconds...")
            time.sleep(wait_seconds)
            return {}
        print(f"  ✗ {artist_name}: API error - {e}")
        return {}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ✗ {artist_name}: Invalid response - {e}")
        return {}


def extract_metadata_from_bio(artist_name: str, festival_bio: str) -> Dict[str, str]:
    """
    Extract metadata from festival bio using AI.
    Only extracts factual information that is explicitly stated in the bio.
    
    Args:
        artist_name: Name of the artist
        festival_bio: Festival bio text (English or Dutch)
        
    Returns:
        Dictionary with extracted metadata (only fields with high confidence)
    """
    prompt = f"""Extract ONLY explicitly stated factual information from this festival bio for artist "{artist_name}". 
Be extremely conservative - only include information that is clearly stated. If not explicitly mentioned, return empty string.

Festival Bio:
{festival_bio}

Extract the following if explicitly stated:
1. Genre: Musical style/genre explicitly mentioned (e.g., "jazz", "indie rock", "psychedelia")
2. Country: Country explicitly mentioned (look for country names or city names that clearly indicate country)
3. Number of People in Act: Group size if stated (e.g., "trio" = 3, "quartet" = 4, "duo" = 2, "solo" = 1)
4. Gender of Front Person: If pronouns (he/his, she/her, they/them) clearly indicate gender, or if explicitly stated
5. Person of Color: ONLY if bio explicitly mentions ethnicity, heritage, or cultural background that clearly indicates (e.g., "Turkish-German", "Nigerian", "Brazilian"). Leave empty if uncertain.

IMPORTANT RULES:
- Country: Accept city names only if they clearly indicate the country (e.g., "Amsterdam" → Netherlands, "Berlin" → Germany, "Istanbul" → Turkey)
- Gender: Only extract if pronouns are used consistently OR if explicitly stated. "Mixed" if multiple genders mentioned.
- Person of Color: Be very cautious. Only mark "Yes" if ethnicity/heritage is explicitly mentioned. Default to empty if unsure.
- If information is ambiguous or not stated, return empty string for that field

Return valid JSON with these exact keys (use empty string if not found):
{{
  "Genre": "...",
  "Country": "...",
  "Number of People in Act": "...",
  "Gender of Front Person": "...",
  "Front Person of Color?": ""
}}"""

    import os
    import requests
    import json
    
    # Check for Azure OpenAI credentials
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    if azure_key and azure_endpoint:
        endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version=2024-02-15-preview"
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_key
        }
        model_name = azure_deployment
    else:
        print(f"  ℹ️  Skipping bio extraction (requires Azure OpenAI credentials)")
        return {}
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a precise data extraction assistant. Extract only explicitly stated facts. Return valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model_name,
        "temperature": 0.1,  # Very low temperature for conservative extraction
        "max_tokens": 300
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON from response
        content = content.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        extracted_data = json.loads(content)
        
        # Filter out empty values
        return {k: v for k, v in extracted_data.items() if v and str(v).strip()}
        
    except Exception as e:
        print(f"  ⚠️  {artist_name}: Bio extraction failed - {e}")
        return {}


def enrich_csv(csv_path: Path, use_ai: bool = False, parallel: bool = False, rating_boost: float = 0.0, artist_name_filter: str = None, force: bool = False):
    """
    Enrich CSV with artist data.
    
    Args:
        csv_path: Path to CSV file
        use_ai: If True, use AI to automatically fill data (requires API setup)
        parallel: If True, process multiple artists concurrently (faster with Azure)
        rating_boost: Rating adjustment for discovery/curated festivals (default 0.0)
        artist_name_filter: If provided, only enrich this specific artist
        force: If True, overwrite existing non-empty fields
    """
    print(f"\n=== Enriching Artist Data ===\n")
    
    if artist_name_filter:
        print(f"ℹ️  Filtering for artist: {artist_name_filter}\n")
    
    if force:
        print(f"⚠️  Force mode enabled: Will overwrite existing fields\n")
    
    if rating_boost != 0.0:
        print(f"ℹ️  Rating boost enabled: +{rating_boost}\n")
    
    headers, rows = load_csv(csv_path)
    enriched_count = 0
    
    # Note: User edits are preserved by not overwriting non-empty fields (unless --force is used)
    # Fields are only enriched if they are currently empty (or if --force is used)
    
    if use_ai and parallel:
        # Parallel processing for faster completion
        import concurrent.futures
        import os
        
        # Determine if we're using Azure (no rate limits) or GitHub Models (rate limited)
        use_azure = bool(os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))
        max_workers = 5 if use_azure else 2  # More parallelism with Azure
        
        artists_to_enrich = [
            (i, row) for i, row in enumerate(rows)
            if (not artist_name_filter or row.get("Artist", "").strip().lower() == artist_name_filter.lower())
            and needs_enrichment(row, force)
        ]
        
        if artists_to_enrich:
            print(f"Processing {len(artists_to_enrich)} artists in parallel (max {max_workers} workers)...)\n")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_artist = {
                    executor.submit(
                        enrich_artist_with_ai, 
                        row.get("Artist", "").strip(), 
                        "" if force else row.get("Bio", "").strip(),  # Don't pass existing bio in force mode
                        rating_boost
                    ): (i, row)
                    for i, row in artists_to_enrich
                }
                
                for future in concurrent.futures.as_completed(future_to_artist):
                    i, row = future_to_artist[future]
                    artist_name = row.get("Artist", "").strip()
                    try:
                        enriched_data = future.result()
                        if enriched_data:
                            enriched_count += 1
                            # Update row with enriched data (only if field is currently empty or force mode)
                            for key, value in enriched_data.items():
                                if key in row and (force or not row.get(key, "").strip()):
                                    # Use festival bio as fallback for Bio when AI has no data
                                    if key == "Bio" and not str(value).strip():
                                        festival_bio_en = row.get("Festival Bio (EN)", "").strip()
                                        festival_bio_nl = row.get("Festival Bio (NL)", "").strip()
                                        festival_bio = festival_bio_en or festival_bio_nl
                                        if festival_bio:
                                            row[key] = f"[using festival bio due to a lack of publicly available data] {festival_bio}"
                                            print(f"    ℹ️  {artist_name}.{key}: Using festival bio as fallback")
                                            
                                            # Try to extract metadata from festival bio
                                            print(f"    → Attempting to extract metadata from festival bio...")
                                            bio_metadata = extract_metadata_from_bio(artist_name, festival_bio)
                                            if bio_metadata:
                                                for meta_key, meta_value in bio_metadata.items():
                                                    if meta_key in row and not row.get(meta_key, "").strip():
                                                        row[meta_key] = meta_value
                                                        print(f"    ✓ Extracted {meta_key}: {meta_value}")
                                        else:
                                            print(f"    ℹ️  {artist_name}.{key}: Left empty (AI had insufficient data, no festival bio)")
                                    # Log if we're filling with empty value and always update the field
                                    elif key in ["AI Rating", "AI Summary"] and not str(value).strip():
                                        print(f"    ℹ️  {artist_name}.{key}: Left empty (AI had insufficient data)")
                                        row[key] = value
                                    else:
                                        row[key] = value
                    except Exception as e:
                        print(f"  ✗ {artist_name}: Unexpected error - {e}")
        
        # Save after parallel processing
        if enriched_count > 0:
            save_csv(csv_path, headers, rows)
            print(f"\n✓ Enriched {enriched_count} artist(s) with AI")
            print("⚠️  Please review and verify AI-generated content")
        return
    
    # Sequential processing (original logic)
    for row in rows:
        artist_name = row.get("Artist", "").strip()
        if not artist_name:
            continue
        
        # Skip if filtering for specific artist
        if artist_name_filter and artist_name.lower() != artist_name_filter.lower():
            continue
        
        if needs_enrichment(row, force):
            enriched_count += 1
            
            if use_ai:
                # AI enrichment (requires API integration)
                # In force mode, don't pass existing bio so AI generates a fresh one
                existing_bio = "" if force else row.get("Bio", "").strip()
                enriched_data = enrich_artist_with_ai(artist_name, existing_bio, rating_boost)
                
                # Update row with enriched data (don't overwrite existing data unless force mode)
                for field, value in enriched_data.items():
                    if field in row:
                        # Only fill if empty or force mode (preserves user edits unless --force)
                        if force or not row[field].strip():
                            # Use festival bio as fallback for Bio when AI has no data
                            if field == "Bio" and not str(value).strip():
                                festival_bio_en = row.get("Festival Bio (EN)", "").strip()
                                festival_bio_nl = row.get("Festival Bio (NL)", "").strip()
                                festival_bio = festival_bio_en or festival_bio_nl
                                if festival_bio:
                                    row[field] = f"[using festival bio due to a lack of publicly available data] {festival_bio}"
                                    print(f"    ℹ️  {artist_name}.{field}: Using festival bio as fallback")
                                    
                                    # Try to extract metadata from festival bio
                                    print(f"    → Attempting to extract metadata from festival bio...")
                                    bio_metadata = extract_metadata_from_bio(artist_name, festival_bio)
                                    if bio_metadata:
                                        for meta_key, meta_value in bio_metadata.items():
                                            if meta_key in row and not row.get(meta_key, "").strip():
                                                row[meta_key] = meta_value
                                                print(f"    ✓ Extracted {meta_key}: {meta_value}")
                                else:
                                    print(f"    ℹ️  {artist_name}.{field}: Left empty (AI had insufficient data, no festival bio)")
                            # Log if we're filling with empty value and always update the field
                            elif field in ["AI Rating", "AI Summary"] and not str(value).strip():
                                print(f"    ℹ️  {artist_name}.{field}: Left empty (AI had insufficient data)")
                                row[field] = value
                            else:
                                row[field] = value
            else:
                print(f"  ⚠️  {artist_name}: Missing data - please fill manually")
    
    if enriched_count > 0:
        if use_ai:
            save_csv(csv_path, headers, rows)
            print(f"\n✓ Enriched {enriched_count} artist(s) with AI-generated data")
            print("⚠️  Please review and verify AI-generated content")
        else:
            print(f"\n⚠️  {enriched_count} artist(s) need manual data entry")
            print("💡 Tip: Use --ai flag to enable automatic enrichment (requires API setup)")
    else:
        print("✓ All artists have complete data!")


def setup_ai_instructions():
    """Print instructions for setting up AI enrichment."""
    print("""
=== AI Enrichment Setup Instructions ===

OPTION 1: Azure OpenAI (Recommended - Better Rate Limits)
----------------------------------------------------------
1. Set Azure OpenAI environment variables:
   Windows (PowerShell):
     $env:AZURE_OPENAI_KEY = "your-azure-key"
     $env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com/"
     $env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
   
   Linux/Mac:
     export AZURE_OPENAI_KEY="your-azure-key"
     export AZURE_OPENAI_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
     export AZURE_OPENAI_DEPLOYMENT="gpt-4o"

2. Run with --ai flag (add --parallel for faster processing):
   python enrich_artists.py --ai --parallel

OPTION 2: GitHub Models (Free, Limited Rate Limits)
----------------------------------------------------
1. Install required package:
   pip install requests

2. Get a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" → "Fine-grained tokens"
   - Name it "Festival Tracker" (or similar)
   - Set expiration (90 days recommended)
   - Under "Repository access": Select "Public Repositories (read-only)"
   - Under "Permissions" → "Contents": Read-only
   - Generate and copy the token

3. Set environment variable:
   Windows (PowerShell):
     $env:GITHUB_TOKEN = "your-github-token"
   
   Linux/Mac:
     export GITHUB_TOKEN="your-github-token"
   
   To persist (add to your profile):
     Windows: Add to $PROFILE
     Linux/Mac: Add to ~/.bashrc or ~/.zshrc

4. Run with --ai flag:
   python enrich_artists.py --ai

NOTE: The script will use Azure OpenAI if configured, otherwise falls back to GitHub Models.
      Always verify AI-generated content for accuracy.
""")


def main():
    """Main enrichment process."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enrich artist data in festival CSV"
    )
    parser.add_argument(
        "--festival",
        type=str,
        default='down-the-rabbit-hole',
        help="Festival identifier (default: down-the-rabbit-hole)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI to automatically enrich data (requires API setup)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Process multiple artists in parallel (faster with Azure OpenAI)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Show AI setup instructions"
    )
    parser.add_argument(
        "--artist",
        type=str,
        help="Enrich only this specific artist (case-insensitive)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty fields (use with caution)"
    )
    
    args = parser.parse_args()
    
    if args.setup:
        setup_ai_instructions()
        return
    
    # Use festival-specific CSV path
    # Try multiple locations
    csv_locations = [
        Path(f"docs/{args.festival}/{args.year}/{args.year}.csv"),
        Path(f"{args.festival}/{args.year}.csv")
    ]
    csv_path = None
    for loc in csv_locations:
        if loc.exists():
            csv_path = loc
            break
    if not csv_path:
        print(f"Error: CSV file not found for {args.festival} {args.year}")
        sys.exit(1)
    
    # Get festival config for rating boost
    festival_config = get_festival_config(args.festival)
    rating_boost = festival_config.rating_boost if festival_config else 0.0
    
    enrich_csv(csv_path, use_ai=args.ai, parallel=args.parallel, rating_boost=rating_boost, artist_name_filter=args.artist, force=args.force)


if __name__ == "__main__":
    main()
