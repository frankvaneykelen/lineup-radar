#!/usr/bin/env python3
"""
Generate an 'about' profile for a festival year.

Creates `about.json` with computed statistics and an AI-written profile (optional),
and a simple `about.html` page summarising the findings.
"""

from __future__ import annotations
import csv
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import argparse

from festival_helpers import get_festival_config
from festival_helpers.ai_client import enrich_with_ai


def load_artists(csv_file: Path) -> list[dict]:
    artists = []
    with csv_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artists.append(row)
    return artists


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def compute_stats(artists: list[dict]) -> dict:
    stats = {}
    stats['total_artists'] = len(artists)

    # Genres
    genre_counts = {}
    dj_count = 0
    for a in artists:
        g = (a.get('Genre') or '').strip()
        name = (a.get('Artist') or '').lower()
        bio = (a.get('Bio') or '')
        if 'dj' in (g.lower() if g else '') or 'dj' in name or 'b2b' in name or 'dj' in bio.lower():
            dj_count += 1
        if g:
            for part in [p.strip() for p in g.split('/') if p.strip()]:
                genre_counts[part] = genre_counts.get(part, 0) + 1

    stats['genre_counts'] = dict(sorted(genre_counts.items(), key=lambda kv: -kv[1]))
    stats['dj_count'] = dj_count

    # Countries
    country_counts = {}
    for a in artists:
        c = (a.get('Country') or '').strip()
        if c:
            for part in [p.strip() for p in c.split('/') if p.strip()]:
                country_counts[part] = country_counts.get(part, 0) + 1
    stats['country_counts'] = dict(sorted(country_counts.items(), key=lambda kv: -kv[1]))

    # Gender and POC
    gender_counts = {}
    poc_counts = {}
    for a in artists:
        gender = (a.get('Gender of Front Person') or 'Unknown').strip() or 'Unknown'
        poc = (a.get('Front Person of Color?') or 'Unknown').strip() or 'Unknown'
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
        poc_counts[poc] = poc_counts.get(poc, 0) + 1
    stats['gender_counts'] = gender_counts
    stats['poc_counts'] = poc_counts

    # Ratings
    ratings = [safe_float(a.get('My rating')) for a in artists]
    ratings = [r for r in ratings if r is not None]
    if ratings:
        stats['average_rating'] = round(sum(ratings) / len(ratings), 2)
        # distribution
        dist = {}
        for r in ratings:
            key = str(int(r))
            dist[key] = dist.get(key, 0) + 1
        stats['rating_distribution'] = dict(sorted(dist.items(), key=lambda kv: -int(kv[0])))
    else:
        stats['average_rating'] = None
        stats['rating_distribution'] = {}

    # Other counts
    stats['has_spotify_links'] = sum(1 for a in artists if (a.get('Spotify link') or '').strip())

    return stats


def compare_with_previous(csv_path: Path, artists: list[dict]) -> dict:
    # Try to find previous year file and compute simple deltas for top genres and avg rating
    prev_stats = {}
    try:
        year = int(csv_path.stem)
    except Exception:
        return {}
    prev_file = csv_path.parent.parent / str(year - 1) / f"{year-1}.csv"
    if prev_file.exists():
        prev_artists = load_artists(prev_file)
        prev_stats_calc = compute_stats(prev_artists)
        current = compute_stats(artists)
        deltas = {}
        for g, cnt in list(current['genre_counts'].items())[:5]:
            prev_cnt = prev_stats_calc.get('genre_counts', {}).get(g, 0)
            deltas[g] = cnt - prev_cnt
        prev_stats = {'prev_year': year-1, 'deltas_top_genres': deltas, 'prev_average_rating': prev_stats_calc.get('average_rating')}
    return prev_stats


def generate_profile_text(config, stats: dict, prev: dict, use_ai: bool = False) -> str:
    # Build a prompt for AI summarization
    prompt_lines = []
    prompt_lines.append(f"Write a short festival profile for '{config.name}' {stats.get('year','')} based on the following statistics:")
    prompt_lines.append(json.dumps(stats, indent=2))
    if prev:
        prompt_lines.append("Compare to the previous year:")
        prompt_lines.append(json.dumps(prev, indent=2))
    prompt_lines.append("Focus on common ground between artists, notable trends, and diversity (gender, country, person-of-color measures). Keep it concise (approx 3 short paragraphs).")
    prompt = "\n\n".join(prompt_lines)
    if use_ai:
        try:
            return enrich_with_ai(prompt, temperature=0.6)
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")

    # Fallback to a simple template (used when --ai isn't provided or AI fails)
    top_genres = ', '.join(list(stats.get('genre_counts', {}).keys())[:3])
    return f"{config.name} {stats.get('year','')} features {stats.get('total_artists')} artists. Top genres include {top_genres}. Average user rating: {stats.get('average_rating')}. Diversity measures: genders={stats.get('gender_counts')}, POC={stats.get('poc_counts')}."


def write_outputs(output_dir: Path, about: dict, html_profile: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'about.json'
    html_path = output_dir / 'about.html'
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(about, f, indent=2, ensure_ascii=False)
    with html_path.open('w', encoding='utf-8') as f:
        f.write(html_profile)
    print(f"✓ Wrote {json_path} and {html_path}")


def render_html(config, stats, profile_text):
    # Simple HTML output
    title = f"About {config.name} {stats.get('year','')}"
    html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\"> 
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>{title}</title>
  <link href=\"../../shared/styles.css\" rel=\"stylesheet\">
</head>
<body>
  <div class=\"container-fluid\">
    <header class=\"page-header lineup-header\"> 
      <div class=\"page-header-content\">
        <h1>{config.name} {stats.get('year','')}</h1>
        <p class=\"subtitle\">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
      </div>
    </header>
    <div class=\"section\">
      <h2>Profile</h2>
      <p>{profile_text.replace('\n','<br/>')}</p>
      <h2>Statistics</h2>
      <pre>{json.dumps(stats, indent=2)}</pre>
    </div>
  </div>
</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--festival', required=True)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--output', default='docs')
    parser.add_argument('--ai', action='store_true', help='Use Azure OpenAI to generate profile')
    args = parser.parse_args()

    config = get_festival_config(args.festival, args.year)
    csv_file = Path(f"docs/{config.slug}/{args.year}/{args.year}.csv")
    if not csv_file.exists():
        print(f"✗ CSV not found: {csv_file}")
        return

    artists = load_artists(csv_file)
    stats = compute_stats(artists)
    stats['year'] = args.year
    prev = compare_with_previous(csv_file, artists)

    profile_text = ''
    # Only call the networked AI when --ai is explicitly provided. Otherwise use fallback text.
    profile_text = generate_profile_text(config, stats, prev, use_ai=args.ai)

    about = {
        'festival': config.slug,
        'name': config.name,
        'year': args.year,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'config_properties': {k: v for k, v in config.__dict__.items() if not k.startswith('_')},
        'stats': stats,
        'previous_year_comparison': prev,
        'ai_profile': profile_text
    }

    out_dir = Path(args.output) / config.slug / str(args.year)
    html = render_html(config, stats, profile_text)
    write_outputs(out_dir, about, html)


if __name__ == '__main__':
    main()
