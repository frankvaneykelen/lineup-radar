"""
Script to auto-generate docs/sw.js for PWA offline caching.
Scans docs/ for all HTML pages and outputs a service worker with ASSETS_TO_CACHE.

Usage:
    python scripts/helpers/generate_sw.py

This will overwrite docs/sw.js with all festival and artist pages included in ASSETS_TO_CACHE.
"""
import os
from pathlib import Path

DOCS_DIR = Path('docs')
SW_PATH = DOCS_DIR / 'sw.js'

HEADER = '''self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('lineup-radar-v1').then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

const ASSETS_TO_CACHE = [
'''

FOOTER = '''];
'''

def find_html_files():
    html_files = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), DOCS_DIR)
                html_files.append(rel_path.replace('\\', '/'))
    return html_files

def main():
    html_files = find_html_files()
    assets_lines = [f"  '/{path}'," for path in html_files]
    sw_content = HEADER + '\n'.join(assets_lines) + '\n' + FOOTER
    with open(SW_PATH, 'w', encoding='utf-8') as f:
        f.write(sw_content)
    print(f"Generated {SW_PATH} with {len(html_files)} HTML pages cached.")

if __name__ == '__main__':
    main()
