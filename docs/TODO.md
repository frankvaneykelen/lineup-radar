# To Do List

- [ ] move all things that can be done a single time, like downloading and translating the bio from the festival website, to the first script that adds (or updates) the CSV data. this means that it will have more columns. running 'python generate_artist_pages.py 2026.csv docs' will be much faster and use less (or no) tokens.
- [ ] apply the above for the links (social media, spotify, youtube, etc) as well
- [ ] add a column for 'festival website url' to the CSV, and use that to scrape data (bio, links, images) only once
- [ ] that link can be scraped from the festival website when the CSV is first created
- [ ] add a column for 'bio translated' to the CSV, and use that to store the AI-generated translation
- [ ] add a column for 'background generated' to the CSV, and use that to store the AI-generated background info
- [ ] add a column for 'social media links scraped' to the CSV, and use that to store whether the links have been scraped already
- [ ] add a column for 'images downloaded' to the CSV, and use that to store whether the images have been downloaded already
- [ ] update the generate_artist_pages.py script to skip downloading/translating/scraping if the relevant columns are already filled
- [ ] improve error handling and logging in all scripts
- [ ] add unit tests for the main functions in each script
- [ ] create a requirements.txt file for easy installation of dependencies  
- [ ] add a CONTRIBUTING.md file with guidelines for contributing to the project
- [ ] set up continuous integration (CI) to automatically run tests on pull requests
- [ ] improve the styling of the generated HTML pages (CSS)
- [ ] add more customization options to the generate_html.py script (e.g., colors, fonts)
- [ ] optimize image sizes for faster loading times on the website

# Not To Do

- [ ] add pagination to the main lineup page if there are many artists