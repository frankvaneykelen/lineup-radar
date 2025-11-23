#!/usr/bin/env python3
"""
Generate the main archive index page (docs/index.html).
This page serves as the landing page linking to all yearly lineups.
"""

import sys
from pathlib import Path
from typing import List


def find_year_folders(docs_dir: Path) -> List[str]:
    """Find all year folders in the docs directory."""
    years = []
    for item in docs_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            # Check if index.html exists in that year folder
            if (item / "index.html").exists():
                years.append(item.name)
    return sorted(years, reverse=True)  # Most recent first


def generate_archive_index(docs_dir: Path):
    """Generate the main archive index page."""
    years = find_year_folders(docs_dir)
    
    if not years:
        print("⚠️  No year folders found with index.html files")
        print("   Generate yearly lineups first with: python generate_html.py")
        sys.exit(1)
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Down The Rabbit Hole - Festival Archive</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="2026/styles.css">
</head>
<body>
    <div class="container-fluid">
        <header class="artist-header lineup-header">
            <div style="width: 60px;"></div>
            <div class="artist-header-content">
                <h1>Down The Rabbit Hole</h1>
                <p class="subtitle">Festival Lineup Archive</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="artist-content container-fluid">
            <div class="row justify-content-center">
                <div class="col-lg-8 col-md-10">
                    <div class="section">
                        <p class="intro" style="font-size: 1.1em; line-height: 1.8; margin-bottom: 2rem;">
                            Welcome to the Down The Rabbit Hole festival archive! 
                            Browse artist lineups, ratings, and appraisals from each year.
                        </p>
                        
                        <div class="year-list">
"""
    
    # Add a button for each year
    for year in years:
        html += f"""                            <div class="year-item mb-3">
                                <a href="{year}/index.html" class="btn btn-primary btn-lg w-100" style="font-size: 1.3em; padding: 20px;">{year} Festival →</a>
                            </div>
"""
    
    html += """                        </div>
                    </div>
                    
                    <div class="section text-center" style="color: #6c757d; padding-top: 2rem; border-top: 1px solid #dee2e6;">
                        <p>Browse artist lineups, ratings, and appraisals from each year.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <footer style="background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em; margin-top: 40px;">
            <button class="dark-mode-toggle" id="darkModeToggle" title="Toggle dark mode">
                <i class="bi bi-moon-fill"></i>
            </button>
            <div>
                <p style="margin-bottom: 15px;">
                    <strong>Content Notice:</strong> These pages combine content scraped from the 
                    <a href="https://downtherabbithole.nl" target="_blank" style="color: #00d9ff; text-decoration: none;">Down The Rabbit Hole festival website</a>
                    with AI-generated content using <strong>Azure OpenAI GPT-4o</strong>.
                </p>
                <p style="margin-bottom: 15px;">
                    <strong>⚠️ Disclaimer:</strong> Information may be incomplete or inaccurate due to automated generation and web scraping. 
                    Please verify critical details on official sources.
                </p>
                <p style="margin-bottom: 0;">
                    Generated with ❤️ • 
                    <a href="https://github.com/frankvaneykelen/down-the-rabbit-hole" target="_blank" style="color: #00d9ff; text-decoration: none;">
                        <i class="bi bi-github"></i> View on GitHub
                    </a>
                </p>
            </div>
        </footer>
    </div>
    <script src="2026/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    output_file = docs_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated archive index: {output_file}")
    print(f"  Found {len(years)} year(s): {', '.join(years)}")


def main():
    """Main entry point."""
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    
    if not docs_dir.exists():
        print(f"✗ Docs directory not found: {docs_dir}")
        print("  Create it first or run generate_html.py")
        sys.exit(1)
    
    generate_archive_index(docs_dir)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
