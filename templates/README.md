# Templates

This directory contains template files used throughout the LineupRadar project.

## `lineup.csv`

Standard CSV template with all columns used across festival lineup files.

### Column Descriptions

**Basic Artist Information:**
- `Artist` - Artist/band name
- `Tagline` - Short promotional tagline from festival (e.g., "The most famous animated band on earth")
- `Genre` - Musical genre(s)
- `Country` - Country of origin
- `Bio` - Artist biography/description

**Performance Details:**
- `Day` - Performance day (e.g., "Friday", "Saturday", "Sunday")
- `Start Time` - Performance start time
- `End Time` - Performance end time
- `Stage` - Stage/venue name

**Links:**
- `Website` - Artist's official website
- `Spotify` - Spotify artist link
- `YouTube` - YouTube channel link
- `Instagram` - Instagram profile link
- `Festival URL` - Link to artist page on festival website

**Media:**
- `Photo URL` - URL to artist photo/image
- `Images Scraped` - Flag indicating if images have been downloaded locally

**Festival Content:**
- `Festival Bio (NL)` - Artist bio from festival website (Dutch)
- `Festival Bio (EN)` - Artist bio from festival website (English translation)
- `Social Links` - JSON object with all social media links

**Personal Notes:**
- `AI Summary` - AI-generated critical assessment
- `AI Rating` - AI-generated rating

**Demographics (for diversity statistics):**
- `Number of People in Act` - Band size
- `Gender of Front Person` - Gender identification
- `Front Person of Color?` - Yes/No flag

**Status:**
- `Cancelled` - Yes/No flag for cancelled performances

### Usage

When creating new festival scrapers, use this template to ensure consistency across all CSV files.

```python
fieldnames = [
    'Artist', 'Tagline', 'Day', 'Start Time', 'End Time', 'Stage',
    'Genre', 'Country', 'Bio', 'Website', 
    'Spotify', 'YouTube', 'Instagram', 'Photo URL',
    'AI Summary', 'AI Rating', 
    'Number of People in Act', 'Gender of Front Person', 'Front Person of Color?',
    'Cancelled', 'Festival URL', 'Festival Bio (NL)', 'Festival Bio (EN)', 
    'Social Links', 'Images Scraped'
]
```

## `settings.json`

Festival-specific settings that should be preserved across regenerations. This file is **never** overwritten by scripts.

### Properties

**Festival Information:**
- `name` - Festival display name
- `description` - Short description of the festival
- `base_url` - Festival website base URL
- `lineup_url` - URL to festival lineup/program page
- `artist_path` - Path segment for artist pages (e.g., "/programma/")

**Configuration:**
- `bio_language` - Language of artist bios on festival website ("Dutch" or "English")
- `rating_boost` - Rating adjustment for discovery festivals (e.g., 1.5 for emerging artists)

**Dates & Venues:**
- `start_date` - Festival start date (ISO format: YYYY-MM-DD)
- `end_date` - Festival end date (ISO format: YYYY-MM-DD)
- `stages` - Array of stage/venue names (optional, used for timetable display)

**Spotify Integration:**
- `official_spotify_playlist` - Official festival Spotify playlist URL
- `spotify_playlist_id` - LineupRadar curated Spotify playlist URL

### Usage

Create a `settings.json` file in each festival year directory (e.g., `docs/alkmaarse-eigenste/2026/settings.json`):

```json
{
  "name": "Alkmaarse Eigenste",
  "base_url": "https://alkmaarseigenste.nl",
  "lineup_url": "https://www.podiumvictorie.nl/programma/alkmaarseigenste2026/",
  "artist_path": "",
  "bio_language": "Dutch",
  "rating_boost": 1.0,
  "description": "A single-day discovery festival in Alkmaar showcasing local and emerging artists.",
  "official_spotify_playlist": "",
  "spotify_playlist_id": "https://open.spotify.com/playlist/7CJ68OA5DWvF2p1Q0HrBOl",
  "start_date": "2026-01-24",
  "end_date": "2026-01-24",
  "stages": ["Grote zaal", "Kleine zaal", "Bezemhok"]
}
```

These settings are automatically merged into `about.json` during generation but are **never modified** by scripts.
