import os
from datetime import datetime, timezone

SITE_ROOT = "https://frankvaneykelen.github.io/lineup-radar/"
DOCS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../docs'))
SITEMAP_PATH = os.path.join(DOCS_DIR, 'sitemap.xml')

EXCLUDE_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.css', '.js', '.ico'}
EXCLUDE_FILES = {'CNAME', 'robots.txt'}


def get_all_urls(docs_dir, site_root):
    urls = []
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.startswith('.') or file in EXCLUDE_FILES:
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTENSIONS:
                continue
            rel_path = os.path.relpath(os.path.join(root, file), docs_dir)
            url_path = rel_path.replace(os.sep, '/')
            urls.append(site_root + url_path)
    return urls


def write_sitemap(urls, out_path):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in urls:
            f.write('  <url>\n')
            f.write(f'    <loc>{url}</loc>\n')
            f.write(f'    <lastmod>{now}</lastmod>\n')
            f.write('    <changefreq>weekly</changefreq>\n')
            f.write('    <priority>0.5</priority>\n')
            f.write('  </url>\n')
        f.write('</urlset>\n')
    print(f"✓ Sitemap written to {out_path} ({len(urls)} URLs)")


if __name__ == "__main__":
    urls = get_all_urls(DOCS_DIR, SITE_ROOT)
    write_sitemap(urls, SITEMAP_PATH)
