# Festival Edition README Maintenance

## Overview

Each festival edition folder (e.g., `docs/best-kept-secret/2026/`) contains a `README.md` file with:
- Festival information (dates, location)
- Quick command examples for all scripts
- CSV structure documentation
- Festival-specific notes

## Automated Generation

READMEs are automatically generated/updated by:

### 1. **When Scraping a Festival**
```powershell
python scripts/scrape_festival.py --festival best-kept-secret --year 2026
```
Automatically generates the README after scraping completes.

### 2. **When Generating About Page**
```powershell
python scripts/generate_about.py --festival best-kept-secret --year 2026
```
Automatically updates the README with current festival data.

### 3. **Manual Generation**

Generate for a specific festival:
```powershell
python scripts/generate_festival_readme.py --festival best-kept-secret --year 2026
```

Generate for all existing festival editions:
```powershell
python scripts/generate_festival_readme.py --all
```

## What Gets Updated Automatically

The README generation script automatically includes:

1. **Festival Dates** - Read from `about.json` (start_date, end_date)
2. **CSV Columns** - Detected from actual CSV file structure
3. **Festival-Specific Notes**:
   - Date format (Date vs Day column)
   - Number of festival days (single-day, multi-day)
   - Bio language (English, Dutch, bilingual)
   - Image scraping method

## Adding a New Festival

When adding a new festival, the README will be automatically created when you:

1. Run the scraper for the first time:
   ```powershell
   python scripts/scrape_festival.py --festival new-festival --year 2026
   ```

2. Or manually generate it:
   ```powershell
   python scripts/generate_festival_readme.py --festival new-festival --year 2026
   ```

## Template Customization

The README template is in `scripts/generate_festival_readme.py`. 

To modify all READMEs:
1. Edit the `README_TEMPLATE` variable in `generate_festival_readme.py`
2. Run: `python scripts/generate_festival_readme.py --all`

## Location Information

Location information is sourced from:
1. `config.location` (if available in festival config)
2. Extracted from `config.description`
3. Falls back to "TBD" if not found

To ensure correct location, add it to the festival config in `festival_helpers/config.py`:
```python
FESTIVALS = {
    'new-festival': {
        'location': 'City, Country',
        # ... other config
    }
}
```

## Best Practices

1. **Run after structural changes** - If you modify CSV columns, run the generator to update documentation
2. **Include in regenerate_all.ps1** - Consider adding README generation to the full regeneration script
3. **Version control** - Commit README changes when festival data structure changes
4. **Review generated content** - Check that dates and locations are correct after first generation
