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
- `My take` - Personal notes/review
- `My rating` - Personal rating

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
    'My take', 'My rating', 
    'Number of People in Act', 'Gender of Front Person', 'Front Person of Color?',
    'Cancelled', 'Festival URL', 'Festival Bio (NL)', 'Festival Bio (EN)', 
    'Social Links', 'Images Scraped'
]
```
