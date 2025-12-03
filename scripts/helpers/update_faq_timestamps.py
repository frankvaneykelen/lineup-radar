#!/usr/bin/env python3
"""
Update FAQ page with current lineup update timestamps.
Reads CSV file modification times and updates the FAQ accordingly.
"""

import os
from pathlib import Path
from datetime import datetime
import re

def get_csv_timestamp(csv_path):
    """Get the last modified timestamp of a CSV file in UTC."""
    if not os.path.exists(csv_path):
        return None
    last_modified = datetime.fromtimestamp(os.path.getmtime(csv_path), tz=datetime.now().astimezone().tzinfo).astimezone(tz=None)
    # Convert to UTC manually
    import time
    utc_timestamp = time.gmtime(os.path.getmtime(csv_path))
    last_modified = datetime(*utc_timestamp[:6])
    return last_modified.strftime("%B %d, %Y %H:%M UTC")

def update_faq_timestamps():
    """Update the FAQ page with current CSV file timestamps."""
    
    # Define festival CSV paths
    festivals = {
        'Down The Rabbit Hole 2026': 'docs/down-the-rabbit-hole/2026/2026.csv',
        'Pinkpop 2026': 'docs/pinkpop/2026/2026.csv',
        'Rock Werchter 2026': 'docs/rock-werchter/2026/2026.csv'
    }
    
    # Get timestamps for each festival
    timestamps = {}
    for name, path in festivals.items():
        timestamp = get_csv_timestamp(path)
        if timestamp:
            timestamps[name] = timestamp
            print(f"✓ {name}: {timestamp}")
        else:
            print(f"✗ {name}: CSV file not found at {path}")
    
    if not timestamps:
        print("\n✗ No festival data found. Cannot update FAQ.")
        return False
    
    # Read current FAQ content
    faq_path = Path('docs/faq.html')
    if not faq_path.exists():
        print(f"\n✗ FAQ file not found at {faq_path}")
        return False
    
    with open(faq_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Build the new timestamp section
    timestamp_items = []
    for name, timestamp in timestamps.items():
        timestamp_items.append(f'                                <li><strong>{name}:</strong> Last updated {timestamp}</li>')
    
    new_timestamp_section = '\n'.join(timestamp_items)
    
    # Find and replace the timestamp section in the FAQ
    # Look for the pattern between <ul> tags in the "How often is the data updated?" section
    pattern = r'(<ul>\s*)<li><strong>Down The Rabbit Hole 2026:</strong>.*?</li>\s*<li><strong>Pinkpop 2026:</strong>.*?</li>\s*<li><strong>Rock Werchter 2026:</strong>.*?</li>'
    
    replacement = rf'\1\n{new_timestamp_section}'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("\n⚠ Warning: Could not find timestamp section to update in FAQ")
        return False
    
    # Write updated content back to FAQ
    with open(faq_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\n✓ Successfully updated FAQ timestamps at {faq_path}")
    return True

if __name__ == '__main__':
    print("\n=== Updating FAQ Timestamps ===\n")
    success = update_faq_timestamps()
    exit(0 if success else 1)
