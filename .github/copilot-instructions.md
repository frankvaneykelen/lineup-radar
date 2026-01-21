# GitHub Copilot Instructions

## Markdown Files

- Always follow Markdown linting rules (MD rules)
- Add blank lines around headings (MD022)
- Add blank lines around lists (MD032)
- Wrap bare URLs in angle brackets `<>` (MD034)
- Follow proper heading hierarchy

## CSV Files

- Use UTF-8 encoding
- Preserve user-edited fields (AI Summary, AI Rating) during updates
- Only add new artists when updating, never remove or modify existing entries
- When an artist cancels, update the "Cancelled" column to "Yes" instead of removing the entry

## JSON Files

### settings.json
- **Never modify** settings.json files - they contain user-defined properties
- Properties: name, description, URLs, dates, stages, spotify playlists, bio_language, rating_boost
- Located in each festival year directory (e.g., `docs/alkmaarse-eigenste/2026/settings.json`)
- These values are automatically merged into about.json during generation
- Values in settings.json override defaults from config.py

### about.json
- Generated file - can be overwritten
- Reads from settings.json for user properties (config_properties, start_date, end_date, stages)
- Contains only generated content: stats, AI profile, generated_at timestamp
- festival, year, and generated_at are metadata; everything else comes from settings.json or is computed

## Code Style

- Follow consistent formatting
- Use descriptive variable and function names
- Add comments for complex logic

## New Scripts

- Always document new scripts in README.md
- Include usage examples with command-line arguments
- Explain when to use each script and what it does
- Add to the appropriate section (Setup, Workflow, or Helpers)
