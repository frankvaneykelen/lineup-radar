#!/usr/bin/env python3
"""
Generate README.md files for festival edition folders.
This ensures consistent documentation across all festivals.
"""

from pathlib import Path
import json
import argparse
import sys

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from festival_helpers import get_festival_config


README_TEMPLATE = """# {festival_name} {year}

**Festival Dates:** {dates}  
**Location:** {location}

## Quick Commands

### Scraping & Data Updates

```powershell
# Scrape the full lineup from the festival website
python scripts/scrape_festival.py --festival {slug} --year {year}

# Fetch Spotify links for all artists
python scripts/fetch_spotify_links.py --festival {slug} --year {year}

# Fetch festival bios and social links
python scripts/fetch_festival_data.py --festival {slug} --year {year}

# Fetch bio for a single artist (useful for testing or updates)
python scripts/fetch_festival_data.py --festival {slug} --year {year} --artist "Artist Name"

# Enrich artist data with AI-generated insights
python scripts/enrich_artists.py --festival {slug} --year {year}

# Manually enrich artist data interactively (prompts for missing fields)
python scripts/manual_enrich_artists.py --festival {slug} --year {year}

# Manually enrich a specific artist
python scripts/manual_enrich_artists.py --festival {slug} --year {year} --artist "Artist Name"
```

### HTML Generation

```powershell
# Generate the main lineup HTML page
python scripts/generate_html.py --festival {slug} --year {year}

# Generate individual artist pages with images
python scripts/generate_artist_pages.py --festival {slug} --year {year}

# Generate the About page with statistics
python scripts/generate_about.py --festival {slug} --year {year}

# Generate About page with AI-generated profile
python scripts/generate_about.py --festival {slug} --year {year} --ai
```

### Spotify Playlists

```powershell
# Generate Spotify playlists for the festival
python scripts/generate_spotify_playlists.py --festival {slug} --year {year}
```

### Full Regeneration

```powershell
# Regenerate all HTML files for this festival (lineup, about, artist pages)
.\\scripts\\regenerate_festival.ps1 -Festival {slug} -Year {year}
```

## Files in This Directory

- **{year}.csv** - Main lineup data with all artist information
- **about.json** - Festival statistics and metadata
- **about.html** - Festival overview and statistics page
- **index.html** - Main lineup page
- **overrides.css** - Festival-specific styling
- **overrides.js** - Festival-specific JavaScript
- **artists/** - Individual artist pages with images

## CSV Structure

The `{year}.csv` file contains these columns:

{csv_columns}

## Notes

- **Personal Data Preserved**: The "AI Summary" and "AI Rating" columns are never overwritten when running update scripts
{additional_notes}
"""


def get_festival_dates(festival_slug, year):
    """Get formatted festival dates from about.json if it exists."""
    about_file = Path(f"docs/{festival_slug}/{year}/about.json")
    if about_file.exists():
        try:
            with about_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                if start_date and end_date:
                    from datetime import datetime
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    
                    if start_date == end_date:
                        return start.strftime('%B %d, %Y')
                    elif start.month == end.month:
                        return f"{start.strftime('%B %d')}-{end.strftime('%d, %Y')}"
                    else:
                        return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}"
        except Exception:
            pass
    
    return "TBD"


def get_csv_columns(csv_file):
    """Get formatted CSV column list from actual CSV file."""
    if not csv_file.exists():
        return "- (CSV file not yet created)"
    
    import csv
    with csv_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    
    # Column descriptions
    descriptions = {
        'Artist': 'Artist/band name',
        'Tagline': 'Festival tagline/description',
        'Date': 'Performance date (YYYY-MM-DD format)',
        'Day': 'Performance day',
        'Start Time': 'Performance start time',
        'End Time': 'Performance end time',
        'Stage': 'Stage name',
        'Genre': 'Musical genre(s)',
        'Country': 'Country of origin',
        'Bio': 'AI-generated or general biography',
        'Website': 'Official website',
        'Spotify': 'Spotify artist link',
        'Spotify link': 'Spotify artist link',
        'YouTube': 'YouTube channel',
        'Instagram': 'Instagram profile',
        'Photo URL': 'Artist photo URL from festival',
        'AI Summary': 'AI-generated critical assessment (preserved on updates)',
        'AI Rating': 'AI-generated rating 1-10 (preserved on updates)',
        'Number of People in Act': 'Band size',
        'Gender of Front Person': 'Gender identification',
        'Front Person of Color?': 'Yes/No',
        'Cancelled': 'Yes/No if performance is cancelled',
        'Festival URL': "Artist's festival page URL",
        'Festival Bio (NL)': 'Dutch bio from festival',
        'Festival Bio (EN)': 'English bio from festival',
        'Social Links': 'JSON with social media links',
        'Images Scraped': 'Yes/No if images downloaded'
    }
    
    lines = []
    for field in fieldnames:
        desc = descriptions.get(field, field)
        lines.append(f"- **{field}** - {desc}")
    
    return '\n'.join(lines)


def get_additional_notes(config, csv_file):
    """Generate festival-specific additional notes."""
    notes = []
    
    # Check if festival has Date column (vs Day)
    if csv_file.exists():
        import csv
        with csv_file.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if 'Date' in fieldnames:
                notes.append("- **Date Format**: Dates are in YYYY-MM-DD format for precise scheduling")
    
    # Check number of days
    about_file = Path(f"docs/{config.slug}/{config.year}/about.json")
    if about_file.exists():
        try:
            with about_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                if start_date and end_date:
                    from datetime import datetime
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    num_days = (end - start).days + 1
                    
                    if num_days == 1:
                        notes.append("- **Single-Day Festival**: This is a one-day event")
                    elif num_days > 3:
                        notes.append(f"- **Multi-Day Festival**: {num_days}-day festival")
        except Exception:
            pass
    
    # Add bio language note
    if hasattr(config, 'bio_language'):
        if config.bio_language == 'English':
            notes.append("- **English Bios**: Festival provides English biographies")
        elif config.bio_language == 'Dutch':
            notes.append("- **Dutch Bios**: Festival provides Dutch biographies")
    
    # Image scraping method
    notes.append("- **Image Downloads**: Artist images are automatically downloaded when generating artist pages")
    
    return '\n'.join(notes) if notes else ""


def generate_readme(festival_slug, year):
    """Generate README.md for a specific festival year."""
    config = get_festival_config(festival_slug, year)
    csv_file = Path(f"docs/{config.slug}/{year}/{year}.csv")
    
    # Get location from config description or default
    location = getattr(config, 'location', 'TBD')
    if not location or location == 'TBD':
        # Extract from description if available
        if hasattr(config, 'description') and config.description:
            # Try to extract location from description
            desc = config.description
            if 'Hilvarenbeek' in desc:
                location = 'Hilvarenbeek, Netherlands'
            elif 'Beuningen' in desc:
                location = 'Beuningen, Netherlands'
            elif 'Landgraaf' in desc:
                location = 'Landgraaf, Netherlands'
            elif 'Werchter' in desc:
                location = 'Werchter, Belgium'
            elif 'Utrecht' in desc:
                location = 'TivoliVredenburg, Utrecht, Netherlands'
    
    readme_content = README_TEMPLATE.format(
        festival_name=config.name,
        year=year,
        dates=get_festival_dates(festival_slug, year),
        location=location,
        slug=config.slug,
        csv_columns=get_csv_columns(csv_file),
        additional_notes=get_additional_notes(config, csv_file)
    )
    
    # Write README
    readme_path = Path(f"docs/{config.slug}/{year}/README.md")
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    
    with readme_path.open('w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ Generated {readme_path}")
    return readme_path


def main():
    parser = argparse.ArgumentParser(description='Generate README.md files for festival editions')
    parser.add_argument('--festival', help='Festival slug (e.g., best-kept-secret)')
    parser.add_argument('--year', type=int, help='Festival year (e.g., 2026)')
    parser.add_argument('--all', action='store_true', help='Generate for all existing festival editions')
    
    args = parser.parse_args()
    
    if args.all:
        # Find all festival edition folders
        docs_path = Path('docs')
        count = 0
        for festival_dir in docs_path.iterdir():
            if festival_dir.is_dir() and festival_dir.name not in ['shared', '.git']:
                for year_dir in festival_dir.iterdir():
                    if year_dir.is_dir() and year_dir.name.isdigit():
                        try:
                            generate_readme(festival_dir.name, int(year_dir.name))
                            count += 1
                        except Exception as e:
                            print(f"✗ Failed to generate README for {festival_dir.name}/{year_dir.name}: {e}")
        
        print(f"\n✓ Generated {count} README files")
    
    elif args.festival and args.year:
        generate_readme(args.festival, args.year)
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/generate_festival_readme.py --festival best-kept-secret --year 2026")
        print("  python scripts/generate_festival_readme.py --all")


if __name__ == '__main__':
    main()
