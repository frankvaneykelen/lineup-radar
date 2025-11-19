#!/usr/bin/env python3
"""
Regenerate all HTML pages from CSV files.
Useful when you want to update all years at once.
"""

import os
import sys
from pathlib import Path
import subprocess

def main():
    """Generate HTML for all CSV files in the repository."""
    
    # Find all CSV files in the current directory (not in subdirectories)
    csv_files = sorted(Path('.').glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in the current directory.")
        return
    
    print(f"\n=== Regenerating HTML for all festival years ===\n")
    
    output_dir = "docs"
    success_count = 0
    
    for csv_file in csv_files:
        # Skip any CSV files that don't look like year files
        if not csv_file.stem.isdigit():
            print(f"⊘ Skipping {csv_file.name} (not a year file)")
            continue
        
        print(f"Processing {csv_file.name}...")
        
        try:
            # Run the generate_html.py script
            result = subprocess.run(
                [sys.executable, "generate_html.py", str(csv_file), output_dir],
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"  ✓ Generated HTML for {csv_file.stem}")
            success_count += 1
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error generating HTML for {csv_file.name}")
            print(f"    {e.stderr}")
    
    print(f"\n✓ Regenerated {success_count} HTML page(s)")
    
    if success_count > 0:
        print(f"\nOutput directory: {output_dir}/")
        print("To preview locally, open: docs/index.html")
        print("\nTo publish changes:")
        print("  git add docs/")
        print("  git commit -m 'Update HTML pages'")
        print("  git push")

if __name__ == "__main__":
    main()
