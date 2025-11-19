# GitHub Pages Setup Guide

This guide will help you publish your festival tracker as a website using GitHub Pages.

## Quick Setup

1. **Commit the generated files:**

   ```powershell
   git add docs/
   git commit -m "Add HTML pages for festival tracker"
   git push
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Click **Settings** (top menu)
   - Click **Pages** (left sidebar)
   - Under "Source", select:
     - Branch: `main`
     - Folder: `/docs`
   - Click **Save**

3. **Wait a few minutes** for GitHub to build your site

4. **Access your site:**
   - It will be available at: `https://yourusername.github.io/repository-name/`
   - For example: `https://frankvaneykelen.github.io/down-the-rabbit-hole/`

## Updating Your Site

Whenever you make changes to your CSV data and want to update the website:

```powershell
# Generate new HTML from updated CSV
python generate_html.py 2026.csv docs

# Commit and push changes
git add docs/
git commit -m "Update festival data"
git push
```

GitHub Pages will automatically rebuild your site within a few minutes.

## Adding New Years

When a new festival year is announced:

1. Create the CSV file (e.g., `2027.csv`)
2. Generate HTML: `python generate_html.py 2027.csv docs`
3. Update `docs/index.html` to add a link to the new year
4. Commit and push

## Customization

You can customize the generated HTML by editing `generate_html.py`:

- Change colors in the CSS section
- Modify the header text
- Adjust column visibility
- Add custom JavaScript features

## Troubleshooting

**Site not showing up?**

- Make sure you've pushed the `docs/` folder to GitHub
- Check that GitHub Pages is enabled in Settings → Pages
- Wait 5-10 minutes after enabling for initial build
- Check the Actions tab for any build errors

**Changes not appearing?**

- Clear your browser cache
- Wait a few minutes for GitHub to rebuild
- Use an incognito/private window to test

**404 error?**

- Make sure the source is set to `/docs` folder (not root `/`)
- Verify that `docs/index.html` exists in your repository

## Custom Domain (Optional)

To use a custom domain like `festival.yourdomain.com`:

1. Add a `CNAME` file in the `docs/` folder with your domain name
2. Configure DNS settings at your domain provider
3. Follow GitHub's custom domain guide: <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site>
