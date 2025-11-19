#!/usr/bin/env python3
"""
Down The Rabbit Hole Festival Tracker - Update Script

This script safely updates the CSV with new artists while preserving user edits.
It tracks which fields have been modified by the user and never overwrites them.
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime


class FestivalTracker:
    """Manages festival artist CSV with safe updates."""
    
    def __init__(self, year: int):
        self.year = year
        self.csv_path = Path(f"{year}.csv")
        self.metadata_dir = Path(".metadata")
        self.metadata_path = self.metadata_dir / f"{year}_metadata.json"
        self.user_edited_fields = {"My take", "My rating"}
        
    def _load_metadata(self) -> Dict:
        """Load metadata tracking user edits."""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"user_edits": {}, "last_updated": None}
    
    def _save_metadata(self, metadata: Dict):
        """Save metadata tracking user edits."""
        self.metadata_dir.mkdir(exist_ok=True)
        metadata["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_csv(self) -> tuple[List[str], List[Dict]]:
        """Load CSV file and return headers and rows."""
        if not self.csv_path.exists():
            return [], []
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        return headers, rows
    
    def _save_csv(self, headers: List[str], rows: List[Dict]):
        """Save CSV file with UTF-8 encoding."""
        with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    
    def track_user_edits(self):
        """
        Scan CSV to detect user edits in protected fields.
        Call this before updating to capture current state.
        """
        metadata = self._load_metadata()
        headers, rows = self._load_csv()
        
        if not rows:
            return
        
        for row in rows:
            artist = row.get("Artist", "")
            if not artist:
                continue
            
            if artist not in metadata["user_edits"]:
                metadata["user_edits"][artist] = {}
            
            # Track non-empty user fields
            for field in self.user_edited_fields:
                value = row.get(field, "").strip()
                if value:
                    metadata["user_edits"][artist][field] = value
        
        self._save_metadata(metadata)
        print(f"✓ Tracked edits for {len(metadata['user_edits'])} artists")
    
    def update_with_new_artists(self, new_artists: List[Dict]):
        """
        Add new artists to CSV while preserving user edits.
        
        Args:
            new_artists: List of artist dictionaries with all fields
        """
        metadata = self._load_metadata()
        headers, existing_rows = self._load_csv()
        
        # Get existing artist names
        existing_artists = {row.get("Artist", "") for row in existing_rows}
        
        # Merge user edits back into existing rows
        for row in existing_rows:
            artist = row.get("Artist", "")
            if artist in metadata["user_edits"]:
                for field, value in metadata["user_edits"][artist].items():
                    row[field] = value
        
        # Add only new artists
        added_count = 0
        for artist_data in new_artists:
            artist_name = artist_data.get("Artist", "")
            if artist_name and artist_name not in existing_artists:
                existing_rows.append(artist_data)
                added_count += 1
        
        if added_count > 0:
            self._save_csv(headers, existing_rows)
            self._save_metadata(metadata)
            print(f"✓ Added {added_count} new artist(s)")
        else:
            print("✓ No new artists to add")
        
        return added_count
    
    def create_initial_csv(self, artists: List[Dict]):
        """Create initial CSV file with artist data."""
        if self.csv_path.exists():
            print(f"! CSV for {self.year} already exists")
            return False
        
        headers = [
            "Artist", "Genre", "Country", "Bio", "My take", "My rating",
            "Spotify link", "Number of People in Act", "Gender of Front Person",
            "Front Person of Color?"
        ]
        
        self._save_csv(headers, artists)
        print(f"✓ Created {self.year}.csv with {len(artists)} artists")
        return True


def main():
    """Example usage of the FestivalTracker."""
    tracker = FestivalTracker(2026)
    
    # Example: Track current user edits before updating
    print("Tracking user edits...")
    tracker.track_user_edits()
    
    # Example: Add new artists (you would fetch these from the website)
    # new_artists = [
    #     {
    #         "Artist": "New Artist Name",
    #         "Genre": "Rock",
    #         "Country": "USA",
    #         ...
    #     }
    # ]
    # tracker.update_with_new_artists(new_artists)


if __name__ == "__main__":
    main()
