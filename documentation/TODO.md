# To Do List

- [x] move all things that can be done a single time, like downloading and translating the bio from the festival website, to the first script that adds (or updates) the CSV data. this means that it will have more columns. running 'python generate_artist_pages.py 2026.csv docs' will be much faster and use less (or no) tokens.
- [x] apply the above for the links (social media, spotify, youtube, etc) as well
- [x] add a column for 'festival website url' to the CSV, and use that to scrape data (bio, links, images) only once
- [x] that link can be scraped from the festival website when the CSV is first created
- [x] add a column for 'bio translated' to the CSV, and use that to store the AI-generated translation
- [ ] add a column for 'background generated' to the CSV, and use that to store the AI-generated background info
- [x] add a column for 'social media links scraped' to the CSV, and use that to store whether the links have been scraped already
- [x] add a column for 'images downloaded' to the CSV, and use that to store whether the images have been downloaded already
- [x] update the generate_artist_pages.py script to skip downloading/translating/scraping if the relevant columns are already filled
- [ ] improve error handling and logging in all scripts
- [x] add unit tests for the main functions in each script
- [ ] create a requirements.txt file for easy installation of dependencies  
- [ ] add a CONTRIBUTING.md file with guidelines for contributing to the project
- [ ] set up continuous integration (CI) to automatically run tests on pull requests
- [ ] improve the styling of the generated HTML pages (CSS)
- [ ] add more customization options to the generate_html.py script (e.g., colors, fonts)
- [ ] optimize image sizes for faster loading times on the website
- [ ] add a To Top button on the index.html pages for easier navigation
- [ ] implement lazy loading for images on the main lineup page
- [ ] Restore the About (from festival) in the original Dutch version scraped from the festival website
- [x] the `badge rounded-pill` are fixed width causing wide columns, make them auto width
- [ ] add a print stylesheet to make the pages printer-friendly
- [ ] make the badges for Genre and Country links to the filtered view for the festival
- [ ] add a FAQ section to the README.md
- [ ] add charts showing the diversity statistics for each year
- [ ] consolidate to a single list of festivals in festival_helpers/config.py and use that everywhere instead of `FESTIVALS = [...]`, `$festivals = @(...)``in multiple places, `## Supported Festivals` in README.md, and elsewhere
- [ ] add missing overrides.css/js files for festivals that don't have them yet
- [ ] add Tagline column to all other festival CSVs (currently only in Best Kept Secret)
- [ ] add Day, Start Time, End Time, Stage columns to all other festival CSVs (currently only in Best Kept Secret)
- [x] consolidate festival-specific scraper scripts into single universal scraper (scrape_festival.py)
- [ ] add Day, Start Time, End Time, Stage columns to all other festival CSVs (currently only in Best Kept Secret)
- [ ] many artists have no Links, maybe the scraping logic can be improved to find more links?

# Not To Do

- [ ] add pagination to the main lineup page if there are many artists
