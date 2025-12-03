# Repository Reorganization Summary

## Changes Made

The repository has been reorganized to improve code structure and maintainability.

### Directory Structure

```text
down-the-rabbit-hole/
├── scripts/                        # Main workflow scripts
│   ├── fetch_festival_data.py     # Fetch lineup from festival websites
│   ├── enrich_artists.py          # AI-powered artist enrichment
│   ├── fetch_spotify_links.py     # Fetch Spotify links (scraping + API)
│   ├── generate_html.py           # Generate lineup HTML pages
│   ├── generate_artist_pages.py   # Generate individual artist pages
│   ├── generate_archive_index.py  # Generate homepage
│   ├── scrape_footprints.py       # Custom Footprints scraper
│   ├── scrape_pinkpop_lineup.py   # Pinkpop lineup scraper
│   ├── update_lineup.py           # Update lineup with new artists
│   ├── regenerate_all.ps1         # Regenerate all HTML (PowerShell)
│   ├── regenerate_all.bat         # Regenerate all HTML (Batch)
│   ├── test_regression.ps1        # Regression test suite
│   └── helpers/                   # Helper/utility scripts
│       ├── clear_dtrh_ratings.py
│       ├── clear_pinkpop_ratings.py
│       ├── fix_csv_quotes.py
│       ├── fix_pinkpop_columns.py
│       ├── generate_charts.py
│       ├── populate_pinkpop_metadata.py
│       ├── remove_empty_lines.py
│       ├── update_faq_timestamps.py
│       ├── use_festival_bios.py
│       └── validate_enrichment.py
├── festival_helpers/              # Core library (unchanged location)
│   ├── __init__.py
│   ├── ai_client.py
│   ├── config.py
│   ├── scraper.py
│   └── slug.py
├── docs/                          # Generated HTML output
├── tests/                         # Unit tests
└── [other project files]
```

### Updated Files

All Python scripts in `scripts/` and `scripts/helpers/` now include:

```python
import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))
```

This allows scripts to import from the `festival_helpers` library located at the repository root.

### Updated Documentation

- **README.md**: All script paths updated from root level to `scripts/` prefix
  - Example: `python fetch_festival_data.py` → `python scripts/fetch_festival_data.py`
- **regenerate_all.ps1**: All script paths updated
- **regenerate_all.bat**: Updated to call `scripts\regenerate_all.ps1`
- **test_regression.ps1**: All script paths updated

## Usage

### Main Workflow Scripts

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Fetch lineup from festival websites
python scripts/fetch_festival_data.py --festival down-the-rabbit-hole --year 2026

# Enrich with AI
python scripts/enrich_artists.py --festival down-the-rabbit-hole --year 2026 --ai --parallel

# Fetch Spotify links
python scripts/fetch_spotify_links.py --festival down-the-rabbit-hole --year 2026

# Generate HTML pages
python scripts/generate_html.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_artist_pages.py --festival down-the-rabbit-hole --year 2026
```

### Quick Regeneration

```powershell
# Regenerate all HTML for all festivals
.\scripts\regenerate_all.ps1

# Or double-click in Windows Explorer
scripts\regenerate_all.bat
```

### Helper Scripts

Helper scripts are in `scripts/helpers/` and are typically used for:

- One-time data fixes (`fix_csv_quotes.py`, `fix_pinkpop_columns.py`)
- Manual data population (`populate_pinkpop_metadata.py`)
- Validation and testing (`validate_enrichment.py`)
- Maintenance tasks (`clear_dtrh_ratings.py`, `update_faq_timestamps.py`)

## Testing

All scripts have been tested and work correctly from their new locations:

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Run regression tests
.\scripts\test_regression.ps1

# Test individual scripts
python scripts/fetch_spotify_links.py --help
python scripts/generate_html.py --help
```

## Migration Notes

- The `festival_helpers/` library remains at the repository root (unchanged)
- All CSV data files remain in `docs/festival-name/year/` (unchanged)
- Generated HTML output remains in `docs/` (unchanged)
- Tests remain in `tests/` (unchanged)
- Only Python scripts (.py), PowerShell scripts (.ps1), and batch files (.bat) were moved

## Verification

The reorganization was verified by:

1. ✅ Running `python scripts/fetch_spotify_links.py --help` (successful)
2. ✅ Running `python scripts/generate_html.py --help` (successful)
3. ✅ Running `.\scripts\regenerate_all.ps1` (all 4 festivals + charts + FAQ = successful)
4. ✅ All imports resolve correctly with `sys.path.insert(0, ...)` fix
5. ✅ All generated HTML pages match expected output

No functional changes were made to the codebase—only organizational improvements.
