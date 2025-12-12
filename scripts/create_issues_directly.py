#!/usr/bin/env python3
"""
Direct issue creation script using GitHub API

This script attempts to create GitHub issues directly using the GitHub REST API.
It will try multiple methods to obtain authentication credentials.
"""

import os
import sys
import subprocess
from typing import List, Tuple, Optional
from urllib.parse import urlparse

# Configuration
DEFAULT_REPO = "frankvaneykelen/lineup-radar"

try:
    import requests
except ImportError:
    print("Error: requests library not found.")
    print("Please install it with: pip install requests")
    sys.exit(1)


def parse_todo_file(todo_path: str) -> List[Tuple[str, int]]:
    """Parse TODO.md and extract unchecked items."""
    with open(todo_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    unchecked_items = []
    in_todo_section = False
    in_not_todo_section = False
    
    for line_num, line in enumerate(lines, start=1):
        if line.strip() == "# To Do List":
            in_todo_section = True
            in_not_todo_section = False
            continue
        elif line.strip() == "# Not To Do":
            in_todo_section = False
            in_not_todo_section = True
            continue
        
        if in_todo_section and not in_not_todo_section:
            if line.strip().startswith('- [ ]'):
                todo_text = line.strip()[6:].strip()
                if todo_text:
                    unchecked_items.append((todo_text, line_num))
    
    return unchecked_items


def get_github_token() -> Optional[str]:
    """Try to obtain GitHub token from environment variables."""
    # Try environment variables
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        return token
    
    # Try gh CLI auth token
    try:
        result = subprocess.run(
            ['gh', 'auth', 'token'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except Exception:
        pass
    
    return None


def create_github_issue(repo: str, title: str, body: str, token: str) -> dict:
    """Create a GitHub issue using the REST API."""
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "title": title,
        "body": body,
        "labels": ["enhancement", "from-todo"]
    }
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    todo_path = os.path.join(repo_path, "documentation", "TODO.md")
    
    # Get repository name from git remote
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=5
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            # Extract owner/repo from git URL using urlparse
            if 'github.com' in remote_url:
                # Handle both HTTPS and SSH URLs
                if remote_url.startswith('git@'):
                    # SSH format: git@github.com:owner/repo.git
                    repo_name = remote_url.split('github.com:')[1].replace('.git', '')
                else:
                    # HTTPS format: https://github.com/owner/repo.git
                    parsed = urlparse(remote_url)
                    repo_name = parsed.path.strip('/').replace('.git', '')
            else:
                repo_name = DEFAULT_REPO
        else:
            repo_name = DEFAULT_REPO
    except Exception:
        repo_name = DEFAULT_REPO
    
    # Get GitHub token
    print("Attempting to obtain GitHub authentication...")
    github_token = get_github_token()
    
    if not github_token:
        print("\n❌ Error: Could not obtain GitHub authentication token")
        print("\nTried:")
        print("  1. GITHUB_TOKEN environment variable")
        print("  2. GH_TOKEN environment variable")
        print("  3. gh CLI authentication")
        print("\nPlease set GITHUB_TOKEN or authenticate with gh CLI:")
        print("  export GITHUB_TOKEN='your-token-here'")
        print("  OR")
        print("  gh auth login")
        sys.exit(1)
    
    print("✓ GitHub token obtained")
    
    # Parse TODO file
    print(f"\nParsing {todo_path}...")
    unchecked_items = parse_todo_file(todo_path)
    
    if not unchecked_items:
        print("No unchecked items found in TODO.md")
        return
    
    print(f"Found {len(unchecked_items)} unchecked TODO items")
    print("=" * 80)
    
    # Create issues
    created_count = 0
    failed_count = 0
    
    for i, (todo_text, line_num) in enumerate(unchecked_items, start=1):
        title = todo_text if len(todo_text) <= 100 else todo_text[:97] + "..."
        body = f"""This task was imported from the TODO list.

**Original TODO item:**
{todo_text}

**Source:** `documentation/TODO.md` (line {line_num})
"""
        
        print(f"\n[{i}/{len(unchecked_items)}] Creating: {title[:60]}...")
        
        try:
            issue = create_github_issue(repo_name, title, body, github_token)
            print(f"  ✓ Created issue #{issue['number']}: {issue['html_url']}")
            created_count += 1
        except requests.exceptions.HTTPError as e:
            print(f"  ✗ Failed: {e}")
            if e.response:
                print(f"    Response: {e.response.text[:200]}")
            failed_count += 1
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  - Created: {created_count} issues")
    print(f"  - Failed: {failed_count} issues")
    print(f"  - Total: {len(unchecked_items)} items")
    
    if created_count > 0:
        print(f"\nView created issues at:")
        print(f"  https://github.com/{repo_name}/issues?q=is%3Aissue+label%3Afrom-todo")


if __name__ == "__main__":
    main()
