#!/usr/bin/env python3
"""
Script to create GitHub issues from unchecked items in TODO.md

This script parses the TODO.md file and creates GitHub issues for all
unchecked items using the GitHub CLI (gh).
"""

import os
import subprocess
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


def create_github_issue_with_gh(title: str, body: str) -> bool:
    """
    Create a GitHub issue using the GitHub CLI (gh).
    
    Args:
        title: Issue title
        body: Issue body/description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use gh CLI to create issue
        result = subprocess.run(
            ["gh", "issue", "create", 
             "--title", title,
             "--body", body,
             "--label", "enhancement,from-todo"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"    Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("    Error: 'gh' command not found. Please install GitHub CLI.")
        return False


def main():
    # Configuration
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    todo_path = os.path.join(repo_path, "documentation", "TODO.md")
    
    # Parse TODO file
    print(f"Parsing {todo_path}...")
    unchecked_items = parse_todo_file(todo_path)
    
    if not unchecked_items:
        print("No unchecked items found in TODO.md")
        return
    
    print(f"\nFound {len(unchecked_items)} unchecked TODO items")
    print("=" * 80)
    
    # Check if gh CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\nError: GitHub CLI (gh) is not installed or not in PATH.")
        print("Please install it from: https://cli.github.com/")
        print("\nAlternatively, you can manually create issues from the list below:")
        print("=" * 80)
        for i, (todo_text, line_num) in enumerate(unchecked_items, start=1):
            print(f"\n{i}. {todo_text}")
            print(f"   (Source: documentation/TODO.md, line {line_num})")
        sys.exit(1)
    
    # Create issues
    created_count = 0
    failed_count = 0
    
    for i, (todo_text, line_num) in enumerate(unchecked_items, start=1):
        # Create a concise title (first 100 chars)
        title = todo_text
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Create issue body with context
        body = f"""This task was imported from the TODO list.

**Original TODO item:**
{todo_text}

**Source:** `documentation/TODO.md` (line {line_num})
"""
        
        print(f"\n[{i}/{len(unchecked_items)}] Creating issue: {title[:60]}...")
        
        if create_github_issue_with_gh(title, body):
            print(f"  ✓ Created successfully")
            created_count += 1
        else:
            print(f"  ✗ Failed to create issue")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  - Created: {created_count} issues")
    print(f"  - Failed: {failed_count} issues")
    print(f"  - Total: {len(unchecked_items)} items")
    
    if created_count > 0:
        print(f"\nView all created issues with: gh issue list --label from-todo")


if __name__ == "__main__":
    main()
