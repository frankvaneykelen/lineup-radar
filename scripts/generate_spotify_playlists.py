"""
Spotify Playlist Generator and Updater for Festival Lineups

Creates and updates Spotify playlists for each festival year with:
- 5 songs per artist (who has a Spotify Link)
- Top 3 tracks by popularity
- First track from 2 most recent singles
- Avoids duplicates between top tracks and singles
- Prefers main artist tracks over features
"""

import os
import sys
import csv
import time
from pathlib import Path
from typing import List, Dict, Optional, Set

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from helpers.config import get_festival_config


def format_retry_time(error_message: str) -> str:
    """
    Format retry time in error messages from seconds to hours and minutes.
    
    Args:
        error_message: The error message that may contain "Retry will occur after: X s"
    
    Returns:
        The error message with formatted retry time, or original message if no match
    """
    import re
    
    # Look for pattern "Retry will occur after: X s"
    match = re.search(r'Retry will occur after:\s*(\d+)\s*s', error_message)
    
    if match:
        seconds = int(match.group(1))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        
        # Format time string
        time_parts = []
        if hours > 0:
            time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if remaining_seconds > 0 or not time_parts:
            time_parts.append(f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}")
        
        formatted_time = ", ".join(time_parts)
        
        # Replace in the original message
        return error_message.replace(
            f"Retry will occur after: {seconds} s",
            f"Retry will occur after: {formatted_time} ({seconds}s)"
        )
    
    return error_message


def setup_spotify_client() -> spotipy.Spotify:
    """Initialize Spotify client with user authentication."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables must be set")
        sys.exit(1)
    
    # Scopes needed for playlist management
    scope = "playlist-modify-public playlist-modify-private"
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=scope
    ))
    
    return sp


def extract_artist_id(spotify_url: str) -> Optional[str]:
    """Extract artist ID from Spotify URL."""
    if not spotify_url or not spotify_url.strip():
        return None
    
    # Format: https://open.spotify.com/artist/{artist_id}
    parts = spotify_url.strip().split('/')
    if len(parts) >= 5 and parts[-2] == 'artist':
        # Remove any query parameters
        artist_id = parts[-1].split('?')[0]
        return artist_id
    
    return None


def update_artist_spotify_link(festival: str, year: int, artist_name: str, new_url: str):
    """Update the Spotify Link for an artist in the CSV file."""
    csv_path = Path(f"docs/{festival}/{year}/{year}.csv")
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Read all rows
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            if row.get('Artist', '').strip() == artist_name:
                row['Spotify Link'] = new_url
            rows.append(row)
    
    # Write back
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  ✅ Updated CSV with new Spotify Link for {artist_name}")


def is_main_artist_track(track: Dict, artist_id: str) -> bool:
    """Check if the track has the artist as the main artist (first in the list)."""
    if not track.get('artists'):
        return False
    
    # Check if our artist is the first (main) artist
    main_artist = track['artists'][0]
    return main_artist['id'] == artist_id


def get_artist_top_tracks(sp: spotipy.Spotify, artist_id: str, artist_name: str, festival: str = None, year: int = None, artists_list: List[Dict] = None, artist_dict: Dict = None):
    """
    Get top 3 tracks for an artist, preferring main artist tracks.
    
    Returns list of track objects with 'id', 'name', 'uri', 'is_main_artist'
    Or tuple (tracks, new_artist_id) if artist was updated
    """
    try:
        # Get artist info first to log the actual Spotify name
        try:
            artist_info = sp.artist(artist_id)
            time.sleep(0.2)  # Rate limiting after API call
        except Exception as e:
            # Catch and format rate limit errors early
            formatted_error = format_retry_time(str(e))
            raise Exception(formatted_error)
        
        spotify_artist_name = artist_info.get('name', artist_name)
        
        # Log if names don't match
        if spotify_artist_name.lower() != artist_name.lower():
            print(f"  ℹ️  Spotify name: '{spotify_artist_name}' (CSV: '{artist_name}')")
        
        # Get top tracks (up to 10)
        try:
            results = sp.artist_top_tracks(artist_id, country='US')
            time.sleep(0.2)  # Rate limiting after API call
        except Exception as e:
            # Catch and format rate limit errors early
            formatted_error = format_retry_time(str(e))
            raise Exception(formatted_error)
        
        tracks = results.get('tracks', [])
        
        if not tracks:
            print(f"  ⚠️  No top tracks found for {artist_name}")
            return []
        
        # Return all tracks with their info (don't filter here, let caller decide)
        all_tracks = []
        
        for track in tracks:
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'uri': track['uri'],
                'popularity': track.get('popularity', 0),
                'is_main_artist': is_main_artist_track(track, artist_id)
            }
            all_tracks.append(track_info)
        
        return all_tracks
    
    except Exception as e:
        error_str = str(e)
        
        # Check if it's a 404 error (artist not found)
        if '404' in error_str or 'not found' in error_str.lower():
            print(f"  ⚠️  Artist not found on Spotify (404 error)")
            print(f"  🔍 Please provide a correct Spotify artist URL for '{artist_name}'")
            print(f"     Search: https://open.spotify.com/search/{artist_name.replace(' ', '%20')}")
            
            new_url = input(f"  📝 Enter new Spotify artist URL (or press Enter to skip): ").strip()
            
            if new_url and festival and year:
                new_artist_id = extract_artist_id(new_url)
                if new_artist_id:
                    update_artist_spotify_link(festival, year, artist_name, new_url)
                    
                    # Update the artist dict if provided
                    if artist_dict is not None:
                        artist_dict['spotify_id'] = new_artist_id
                        artist_dict['spotify_url'] = new_url
                    
                    print(f"  🔄 Retrying with new artist ID: {new_artist_id}")
                    # Retry with new ID and return both tracks and new ID
                    tracks = get_artist_top_tracks(sp, new_artist_id, artist_name, festival, year, artists_list, artist_dict)
                    return (tracks, new_artist_id) if not isinstance(tracks, tuple) else tracks
                else:
                    print(f"  ❌ Invalid Spotify URL format")
            
            return []
        else:
            # Format retry time if present in error message
            formatted_error = format_retry_time(error_str)
            print(f"  ❌ Error getting top tracks for {artist_name}: {formatted_error}")
            return []


def get_artist_singles(sp: spotipy.Spotify, artist_id: str, artist_name: str) -> List[Dict]:
    """
    Get singles for an artist, sorted by release date (most recent first).
    
    Returns list of album objects representing singles.
    """
    try:
        singles = []
        
        # Get singles (limit 50)
        try:
            results = sp.artist_albums(artist_id, album_type='single', limit=50)
            time.sleep(0.2)  # Rate limiting after API call
        except Exception as e:
            # Catch and format rate limit errors early
            formatted_error = format_retry_time(str(e))
            raise Exception(formatted_error)
        
        for album in results.get('items', []):
            # Only include if artist is the main artist
            if album['artists'] and album['artists'][0]['id'] == artist_id:
                singles.append({
                    'id': album['id'],
                    'name': album['name'],
                    'release_date': album.get('release_date', ''),
                    'uri': album['uri']
                })
        
        # Sort by release date (most recent first)
        singles.sort(key=lambda x: x['release_date'], reverse=True)
        
        return singles
    
    except Exception as e:
        formatted_error = format_retry_time(str(e))
        print(f"  ❌ Error getting singles for {artist_name}: {formatted_error}")
        return []


def get_first_track_from_single(sp: spotipy.Spotify, single_id: str) -> Optional[Dict]:
    """Get the first track from a single/album."""
    try:
        try:
            album = sp.album(single_id)
            time.sleep(0.2)  # Rate limiting after API call
        except Exception as e:
            # Catch and format rate limit errors early
            formatted_error = format_retry_time(str(e))
            raise Exception(formatted_error)
        tracks = album.get('tracks', {}).get('items', [])
        
        if tracks:
            track = tracks[0]
            return {
                'id': track['id'],
                'name': track['name'],
                'uri': track['uri']
            }
        
        return None
    
    except Exception as e:
        formatted_error = format_retry_time(str(e))
        print(f"  ⚠️  Error getting track from single: {formatted_error}")
        return None


def select_tracks_for_artist(sp: spotipy.Spotify, artist_id: str, artist_name: str, festival: str = None, year: int = None, artists_list: List[Dict] = None, artist_dict: Dict = None) -> List[str]:
    """
    Select 5 tracks for an artist following the rules:
    1. Top 3 tracks (by popularity)
    2. First track from 2 most recent singles
    3. Avoid duplicates
    4. Fill with top songs if not enough singles
    5. Prefer main artist tracks
    
    Returns list of track URIs.
    """
    print(f"\n🎵 Processing: {artist_name}")
    
    # Get top tracks (this may update the CSV and return a new artist_id)
    result = get_artist_top_tracks(sp, artist_id, artist_name, festival, year, artists_list, artist_dict)
    
    # Check if we got a new artist_id (when CSV was updated)
    if isinstance(result, tuple):
        top_tracks, new_artist_id = result
        artist_id = new_artist_id
    else:
        top_tracks = result
    
    print(f"  ✓ Found {len(top_tracks)} top tracks")
    
    # Get singles
    singles = get_artist_singles(sp, artist_id, artist_name)
    print(f"  ✓ Found {len(singles)} singles")
    
    # Start with top 3 tracks (prefer main artist, but include features if needed)
    selected_track_ids: Set[str] = set()
    selected_track_names: Set[str] = set()  # Track names for duplicate detection
    selected_uris: List[str] = []
    
    # First add main artist tracks
    main_tracks = [t for t in top_tracks if t.get('is_main_artist', True)]
    for track in main_tracks[:3]:
        selected_track_ids.add(track['id'])
        selected_track_names.add(track['name'].lower())  # Normalize for comparison
        selected_uris.append(track['uri'])
        print(f"  ✓ Top track: {track['name']}")
    
    # If we don't have 3 yet, add featuring tracks
    if len(selected_uris) < 3:
        featured_tracks = [t for t in top_tracks if not t.get('is_main_artist', True)]
        for track in featured_tracks[:3 - len(selected_uris)]:
            selected_track_ids.add(track['id'])
            selected_track_names.add(track['name'].lower())
            selected_uris.append(track['uri'])
            print(f"  ✓ Top track (feat): {track['name']}")
    
    # Try to add first tracks from most recent singles
    singles_added = 0
    single_idx = 0
    
    while singles_added < 2 and single_idx < len(singles):
        single = singles[single_idx]
        track = get_first_track_from_single(sp, single['id'])
        
        # Skip if duplicate by ID or name, or if it's a remix
        is_duplicate_id = track and track['id'] in selected_track_ids
        is_duplicate_name = track and track['name'].lower() in selected_track_names
        is_remix = track and 'remix' in track['name'].lower()
        
        if track and not is_duplicate_id and not is_duplicate_name and not is_remix:
            selected_track_ids.add(track['id'])
            selected_track_names.add(track['name'].lower())
            selected_uris.append(track['uri'])
            singles_added += 1
            print(f"  ✓ Added single track: {track['name']}")
        elif track and is_remix:
            print(f"  ⊗ Skipped remix: {track['name']}")
        elif track and (is_duplicate_id or is_duplicate_name):
            print(f"  ⊗ Skipped duplicate: {track['name']}")
        
        single_idx += 1
        time.sleep(0.5)  # Rate limiting - prevent API throttling
    
    # Fill remaining slots with any available tracks from top tracks
    if len(selected_uris) < 5:
        for track in top_tracks:
            if track['id'] not in selected_track_ids and track['name'].lower() not in selected_track_names:
                selected_track_ids.add(track['id'])
                selected_track_names.add(track['name'].lower())
                selected_uris.append(track['uri'])
                track_type = "main" if track.get('is_main_artist', True) else "feat"
                print(f"  ✓ Filler track ({track_type}): {track['name']}")
                
                if len(selected_uris) >= 5:
                    break
    
    print(f"  ✅ Selected {len(selected_uris)} tracks total")
    return selected_uris[:5]


def load_festival_artists(festival: str, year: int) -> List[Dict]:
    """Load artists from festival CSV who have Spotify links."""
    csv_path = Path(f"docs/{festival}/{year}/{year}.csv")
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return []
    
    artists = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        total = len(reader)
        for idx, row in enumerate(reader, 1):
            artist_name = row.get('Artist', '') or ''
            artist_name = artist_name.strip()
            spotify_link = row.get('Spotify Link', '') or ''
            spotify_link = spotify_link.strip()

            if not spotify_link and spotify_link != 'NOT ON SPOTIFY':
                print(f"\n⚠️  No Spotify Link found for '{artist_name}' [{idx}/{total}]")
                print(f"  🔍 Search: https://open.spotify.com/search/{artist_name.replace(' ', '%20')}")
                print(f"  📝 Enter Spotify artist URL (or 'NOT ON SPOTIFY' if not available, or press Enter to skip): ", end='', flush=True)

                new_url = input().strip()

                if new_url:
                    if new_url.upper() == "NOT ON SPOTIFY":
                        update_artist_spotify_link(festival, year, artist_name, "NOT ON SPOTIFY")
                        print(f"  ℹ️  Marked {artist_name} as not on Spotify")
                    else:
                        artist_id = extract_artist_id(new_url)
                        if artist_id:
                            update_artist_spotify_link(festival, year, artist_name, new_url)
                            artists.append({
                                'name': artist_name,
                                'spotify_id': artist_id,
                                'spotify_url': new_url
                            })
                            print(f"  ✅ Added {artist_name} to playlist")
                        else:
                            print(f"  ❌ Invalid Spotify URL format, skipping {artist_name}")
                else:
                    print(f"  ⏭️  Skipping {artist_name}")
                continue

            # Skip artists marked as not on Spotify
            if spotify_link.upper() == "NOT ON SPOTIFY":
                continue

            artist_id = extract_artist_id(spotify_link)
            if artist_id:
                artists.append({
                    'name': artist_name,
                    'spotify_id': artist_id,
                    'spotify_url': spotify_link
                })
    
    return artists


def find_or_create_playlist(sp: spotipy.Spotify, playlist_name: str, description: str) -> str:
    """Find existing playlist or create new one. Returns playlist ID."""
    user_id = sp.current_user()['id']
    
    # Check existing playlists
    playlists = sp.current_user_playlists(limit=50)
    
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            print(f"✓ Found existing playlist: {playlist_name}")
            return playlist['id']
    
    # Create new playlist
    playlist = sp.user_playlist_create(
        user_id,
        playlist_name,
        public=True,
        description=description
    )
    
    print(f"✓ Created new playlist: {playlist_name}")
    return playlist['id']


def update_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: List[str]):
    """Replace all tracks in a playlist with new ones."""
    # Spotify allows max 100 tracks per request
    # Clear existing tracks first
    sp.playlist_replace_items(playlist_id, [])
    
    # Add tracks in batches of 100
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i+100]
        sp.playlist_add_items(playlist_id, batch)
        print(f"  ✓ Added {len(batch)} tracks (batch {i//100 + 1})")


def generate_playlist_for_festival(sp: spotipy.Spotify, festival: str, year: int):
    """Generate or update Spotify playlist for a festival year."""
    print(f"\n{'='*60}")
    print(f"🎪 Festival: {festival.upper()} {year}")
    print(f"{'='*60}")
    
    # Load festival config for display name
    try:
        config = get_festival_config(festival, year)
        festival_display_name = config.name
    except:
        festival_display_name = festival.replace('-', ' ').title()
    
    # Load artists
    artists = load_festival_artists(festival, year)
    
    if not artists:
        print(f"❌ No artists with Spotify links found for {festival} {year}")
        return
    
    print(f"\n✓ Found {len(artists)} artists with Spotify links")
    
    # Collect tracks
    all_track_uris = []
    
    for artist in artists:
        try:
            # Check if we need to reload artist info from CSV (in case it was updated)
            track_uris = select_tracks_for_artist(sp, artist['spotify_id'], artist['name'], festival, year, artists, artist)
            all_track_uris.extend(track_uris)
            time.sleep(1.0)  # Rate limiting - prevent API throttling
        except Exception as e:
            formatted_error = format_retry_time(str(e))
            print(f"  ❌ Error processing {artist['name']}: {formatted_error}")
    
    if not all_track_uris:
        print(f"\n❌ No tracks collected for {festival} {year}")
        return
    
    print(f"\n✅ Collected {len(all_track_uris)} total tracks for {len(artists)} artists")
    
    # Create/find playlist
    playlist_name = f"LineupRadar - {festival_display_name} {year}"
    description = f"Lineup playlist for {festival_display_name} {year} - Generated with 5 tracks per artist (top 3 tracks + most recent singles)"
    
    playlist_id = find_or_create_playlist(sp, playlist_name, description)
    
    # Update playlist
    print(f"\n📝 Updating playlist...")
    update_playlist(sp, playlist_id, all_track_uris)
    
    print(f"\n✅ Playlist updated successfully!")
    print(f"🔗 https://open.spotify.com/playlist/{playlist_id}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Spotify playlists for festival lineups')
    parser.add_argument('--festival', required=True, help='Festival name (e.g., down-the-rabbit-hole, pinkpop, footprints)')
    parser.add_argument('--year', type=int, required=True, help='Festival year')
    
    args = parser.parse_args()
    
    # Setup Spotify client
    print("🔐 Authenticating with Spotify...")
    sp = setup_spotify_client()
    print("✅ Authentication successful!")
    
    # Generate playlist
    generate_playlist_for_festival(sp, args.festival, args.year)


if __name__ == '__main__':
    main()
