#!/usr/bin/env python3
"""
Script to export TODO items to formats that can be easily imported into GitHub

This script parses the TODO.md file and exports unchecked items in various formats:
- GitHub CLI commands
- CSV for bulk import
- Markdown for copy-paste
"""

import os
import csv
import sys
from typing import List, Tuple


def parse_todo_file(todo_path: str) -> List[Tuple[str, int]]:
    """
    Parse TODO.md and extract unchecked items from the main 'To Do List' section.
    
    Args:
        todo_path: Path to the TODO.md file
        
    Returns:
        List of tuples (todo_text, line_number)
    """
    with open(todo_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    unchecked_items = []
    in_todo_section = False
    in_not_todo_section = False
    
    for line_num, line in enumerate(lines, start=1):
        # Check for section headers
        if line.strip() == "# To Do List":
            in_todo_section = True
            in_not_todo_section = False
            continue
        elif line.strip() == "# Not To Do":
            in_todo_section = False
            in_not_todo_section = True
            continue
        
        # Only process unchecked items in the "To Do List" section
        if in_todo_section and not in_not_todo_section:
            if line.strip().startswith('- [ ]'):
                # Extract the todo text (remove the checkbox part)
                todo_text = line.strip()[6:].strip()
                if todo_text:  # Only add non-empty items
                    unchecked_items.append((todo_text, line_num))
    
    return unchecked_items


def export_as_shell_script(items: List[Tuple[str, int]], output_path: str):
    """Export as a shell script with gh CLI commands"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('#!/bin/bash\n')
        f.write('# Auto-generated script to create GitHub issues from TODO.md\n')
        f.write('# Run this script to create all issues at once\n\n')
        f.write('set -e  # Exit on error\n\n')
        
        for todo_text, line_num in items:
            title = todo_text if len(todo_text) <= 100 else todo_text[:97] + "..."
            body = f"This task was imported from the TODO list.\\n\\n**Original TODO item:**\\n{todo_text}\\n\\n**Source:** `documentation/TODO.md` (line {line_num})"
            
            # Escape single quotes for shell
            title_escaped = title.replace("'", "'\"'\"'")
            body_escaped = body.replace("'", "'\"'\"'")
            
            f.write(f"echo 'Creating: {title[:50]}...'\n")
            f.write(f"gh issue create --title '{title_escaped}' --body '{body_escaped}' --label 'enhancement,from-todo'\n\n")
    
    print(f"✓ Shell script created: {output_path}")
    print(f"  Run with: bash {output_path}")


def export_as_markdown(items: List[Tuple[str, int]], output_path: str):
    """Export as markdown with formatted issue descriptions"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# GitHub Issues from TODO.md\n\n')
        f.write(f'Found {len(items)} unchecked TODO items to convert into issues.\n\n')
        f.write('---\n\n')
        
        for i, (todo_text, line_num) in enumerate(items, start=1):
            title = todo_text if len(todo_text) <= 100 else todo_text[:97] + "..."
            
            f.write(f'## Issue {i}: {title}\n\n')
            f.write('**Title:**\n')
            f.write(f'```\n{title}\n```\n\n')
            f.write('**Body:**\n')
            f.write('```markdown\n')
            f.write(f'This task was imported from the TODO list.\n\n')
            f.write(f'**Original TODO item:**\n')
            f.write(f'{todo_text}\n\n')
            f.write(f'**Source:** `documentation/TODO.md` (line {line_num})\n')
            f.write('```\n\n')
            f.write('**Labels:** `enhancement`, `from-todo`\n\n')
            f.write('---\n\n')
    
    print(f"✓ Markdown file created: {output_path}")
    print(f"  Review and copy-paste issue details from this file")


def export_as_csv(items: List[Tuple[str, int]], output_path: str):
    """Export as CSV for bulk import tools"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Body', 'Labels', 'Source Line'])
        
        for todo_text, line_num in items:
            title = todo_text if len(todo_text) <= 100 else todo_text[:97] + "..."
            body = f"This task was imported from the TODO list.\n\n**Original TODO item:**\n{todo_text}\n\n**Source:** `documentation/TODO.md` (line {line_num})"
            labels = "enhancement,from-todo"
            
            writer.writerow([title, body, labels, line_num])
    
    print(f"✓ CSV file created: {output_path}")
    print(f"  Import using GitHub's bulk import tools or scripts")


def main():
    # Configuration
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    todo_path = os.path.join(repo_path, "documentation", "TODO.md")
    output_dir = os.path.join(repo_path, "tmp")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse TODO file
    print(f"Parsing {todo_path}...")
    unchecked_items = parse_todo_file(todo_path)
    
    if not unchecked_items:
        print("No unchecked items found in TODO.md")
        return
    
    print(f"\nFound {len(unchecked_items)} unchecked TODO items")
    print("=" * 80)
    
    # Export in different formats
    export_as_shell_script(unchecked_items, os.path.join(output_dir, "create_issues.sh"))
    export_as_markdown(unchecked_items, os.path.join(output_dir, "issues_to_create.md"))
    export_as_csv(unchecked_items, os.path.join(output_dir, "issues.csv"))
    
    print("\n" + "=" * 80)
    print("Export complete! You can now:")
    print("  1. Run the shell script: bash tmp/create_issues.sh")
    print("  2. Review the markdown file: tmp/issues_to_create.md")
    print("  3. Use the CSV for bulk import: tmp/issues.csv")


if __name__ == "__main__":
    main()
