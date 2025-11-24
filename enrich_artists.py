#!/usr/bin/env python3
"""
AI-powered artist data enrichment for Down The Rabbit Hole Festival Tracker

Uses AI to automatically fill in artist details (genre, country, bio, etc.)
when new artists are added to the CSV.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List
import json


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


def needs_enrichment(row: Dict) -> bool:
    """Check if artist row needs data enrichment."""
    essential_fields = ["Genre", "Country", "Bio", "My take", "My rating"]
    return any(not row.get(field, "").strip() for field in essential_fields)


def create_enrichment_prompt(artist_name: str) -> str:
    """Create a prompt for AI to enrich artist data."""
    return f"""Provide comprehensive information about the musical artist "{artist_name}" in JSON format with these exact fields:

{{
    "Genre": "primary genre(s), separated by /",
    "Country": "country of origin (use short names: UK, USA, DR Congo, etc.)",
    "Bio": "concise 1-2 sentence biography focusing on their music style and achievements",
    "My take": "brief critical assessment of their artistry and live performance potential, informed by reviews and consensus (or empty string if insufficient info)",
    "My rating": "rating from 1-10 based on critical acclaim, live reputation, and artistic significance (or empty string if insufficient info)",
    "Spotify link": "full Spotify artist URL (https://open.spotify.com/artist/...)",
    "Number of People in Act": "number as integer, or empty if solo/varies",
    "Gender of Front Person": "Male/Female/Mixed/Non-binary",
    "Front Person of Color?": "Yes/No"
}}

CRITICAL GUIDELINES:
- ONLY provide information if you have reliable, verifiable data about this artist
- If the artist is mysterious, unknown, or you cannot find reliable information: leave Bio, My take, My rating, and demographic fields EMPTY
- DO NOT hallucinate or guess about artist gender, demographics, or biographical details
- Bio should be factual, concise, and music-focused - or empty if insufficient data
- My take should reflect critical consensus and live performance reviews (1-2 sentences) - or empty if insufficient data
- My rating should be objective, based on critical acclaim and festival suitability (integer 1-10) - or empty if insufficient data
- Use official Spotify URLs only
- For groups with multiple frontpeople, use "Mixed" for gender
- Be accurate about demographics; use "Yes" for Front Person of Color only if confirmed, otherwise "No"
- Leave "Number of People in Act" empty for solo artists or when it varies (DJs, producers)
- Use abbreviated country names: "UK" not "United Kingdom", "USA" not "United States", "DR Congo" not "Democratic Republic of the Congo"
- When in doubt about ANY field, leave it empty rather than guessing

Return ONLY valid JSON, no additional text."""


def enrich_artist_with_ai(artist_name: str) -> Dict[str, str]:
    """
    Use Azure OpenAI or GitHub Models API to enrich artist data.
    
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
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
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
    
    prompt = create_enrichment_prompt(artist_name)
    
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
        rating = artist_data.get("My rating", "")
        my_take = artist_data.get("My take", "")
        
        # Convert rating to string and handle edge cases
        if rating == 0 or rating == "0":
            print(f"  ⚠️  {artist_name}: AI returned rating 0 (not enough publicly available critical reviews or performance data) - setting to empty")
            artist_data["My rating"] = ""
        elif not str(rating).strip():
            print(f"  ⚠️  {artist_name}: AI returned empty rating (not enough publicly available critical reviews or performance data)")
            artist_data["My rating"] = ""
        
        if not my_take.strip():
            print(f"  ⚠️  {artist_name}: AI returned empty 'My take' (not enough publicly available critical reviews or performance data)")
        
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


def enrich_csv(csv_path: Path, use_ai: bool = False, parallel: bool = False):
    """
    Enrich CSV with artist data.
    
    Args:
        csv_path: Path to CSV file
        use_ai: If True, use AI to automatically fill data (requires API setup)
        parallel: If True, process multiple artists concurrently (faster with Azure)
    """
    print(f"\n=== Enriching Artist Data ===\n")
    
    headers, rows = load_csv(csv_path)
    enriched_count = 0
    
    # Track metadata to preserve user edits
    from festival_tracker import FestivalTracker
    tracker = FestivalTracker(2026)  # TODO: make year dynamic
    metadata = tracker._load_metadata()
    
    if use_ai and parallel:
        # Parallel processing for faster completion
        import concurrent.futures
        import os
        
        # Determine if we're using Azure (no rate limits) or GitHub Models (rate limited)
        use_azure = bool(os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))
        max_workers = 5 if use_azure else 2  # More parallelism with Azure
        
        artists_to_enrich = [(i, row) for i, row in enumerate(rows) if needs_enrichment(row)]
        
        if artists_to_enrich:
            print(f"Processing {len(artists_to_enrich)} artists in parallel (max {max_workers} workers)...\n")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_artist = {
                    executor.submit(enrich_artist_with_ai, row.get("Artist", "").strip()): (i, row)
                    for i, row in artists_to_enrich
                }
                
                for future in concurrent.futures.as_completed(future_to_artist):
                    i, row = future_to_artist[future]
                    artist_name = row.get("Artist", "").strip()
                    try:
                        enriched_data = future.result()
                        if enriched_data:
                            enriched_count += 1
                            # Update row with enriched data
                            for key, value in enriched_data.items():
                                if key in row and not row.get(key, "").strip():
                                    # Check if user has edited this field
                                    if artist_name in metadata.get("edited_artists", {}):
                                        user_edits = metadata["edited_artists"][artist_name].get("fields", [])
                                        if key not in user_edits:
                                            # Log if we're filling with empty value
                                            if key in ["My rating", "My take"] and not str(value).strip():
                                                print(f"    ℹ️  {artist_name}.{key}: Left empty (AI had insufficient data)")
                                            row[key] = value
                                    else:
                                        # Log if we're filling with empty value
                                        if key in ["My rating", "My take"] and not str(value).strip():
                                            print(f"    ℹ️  {artist_name}.{key}: Left empty (AI had insufficient data)")
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
        
        if needs_enrichment(row):
            enriched_count += 1
            
            if use_ai:
                # AI enrichment (requires API integration)
                enriched_data = enrich_artist_with_ai(artist_name)
                
                # Update row with enriched data (don't overwrite existing data OR user edits)
                for field, value in enriched_data.items():
                    if field in row:
                        # Check if user has edited this field
                        user_edited = (
                            artist_name in metadata.get("user_edits", {}) and
                            field in metadata["user_edits"][artist_name]
                        )
                        
                        # Only fill if empty AND not user-edited
                        if not row[field].strip() and not user_edited:
                            # Log if we're filling with empty value (AI had insufficient data)
                            if field in ["My rating", "My take"] and not str(value).strip():
                                print(f"    ℹ️  {artist_name}.{field}: Left empty (AI had insufficient data)")
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
    
    args = parser.parse_args()
    
    if args.setup:
        setup_ai_instructions()
        return
    
    csv_path = Path(f"{args.year}.csv")
    
    enrich_csv(csv_path, use_ai=args.ai, parallel=args.parallel)


if __name__ == "__main__":
    main()
