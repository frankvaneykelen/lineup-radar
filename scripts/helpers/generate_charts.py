"""
Generate a charts page comparing festival lineups.
"""

import csv
from pathlib import Path
import json
import sys
# helpers module is in the same directory

from menu import generate_hamburger_menu

def load_festival_data(csv_path):
    """Load and analyze festival data from CSV."""
    artists = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artists.append(row)
    
    return artists

def analyze_gender(artists):
    """Analyze gender distribution."""
    gender_counts = {}
    total = 0
    
    for artist in artists:
        gender = artist.get('Gender of Front Person', '').strip()
        if gender:
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
            total += 1
    
    return gender_counts, total

def analyze_poc(artists):
    """Analyze POC representation."""
    poc_counts = {'Yes': 0, 'No': 0, 'Unknown': 0}
    
    for artist in artists:
        poc = artist.get('Front Person of Color?', '').strip()
        if poc in poc_counts:
            poc_counts[poc] += 1
        elif not poc:
            poc_counts['Unknown'] += 1
    
    return poc_counts

def analyze_ratings(artists):
    """Analyze rating distribution."""
    rating_counts = {}
    
    for artist in artists:
        rating = artist.get('AI Rating', '').strip()
        if rating:
            try:
                rating_int = int(float(rating))
                rating_counts[rating_int] = rating_counts.get(rating_int, 0) + 1
            except ValueError:
                pass
    
    return rating_counts

def analyze_countries(artists):
    """Analyze country distribution."""
    country_counts = {}
    
    # Normalization mapping
    country_mapping = {
        'United States': 'USA',
        'United Kingdom': 'UK'
    }
    
    for artist in artists:
        country = artist.get('Country', '').strip()
        if country:
            # Normalize country names
            country = country_mapping.get(country, country)
            country_counts[country] = country_counts.get(country, 0) + 1
    
    return country_counts

def generate_charts_page():
    """Generate the charts comparison page."""
    
    # Paths to CSV files
    festivals = {
        'Down The Rabbit Hole': {
            'csv': Path('docs/down-the-rabbit-hole/2026/2026.csv'),
            'slug': 'down-the-rabbit-hole',
            'color': '#FF6B6B'
        },
        'Pinkpop': {
            'csv': Path('docs/pinkpop/2026/2026.csv'),
            'slug': 'pinkpop',
            'color': '#4ECDC4'
        },
        'Rock Werchter': {
            'csv': Path('docs/rock-werchter/2026/2026.csv'),
            'slug': 'rock-werchter',
            'color': '#95E1D3'
        },
        'Footprints': {
            'csv': Path('docs/footprints/2026/2026.csv'),
            'slug': 'footprints',
            'color': '#FFA07A'
        },
        'Best Kept Secret': {
            'csv': Path('docs/best-kept-secret/2026/2026.csv'),
            'slug': 'best-kept-secret',
            'color': '#FFD700'
        }
    }
    
    # Collect data for all festivals
    festival_data = {}
    
    for name, info in festivals.items():
        if info['csv'].exists():
            artists = load_festival_data(info['csv'])
            gender_counts, gender_total = analyze_gender(artists)
            poc_counts = analyze_poc(artists)
            rating_counts = analyze_ratings(artists)
            country_counts = analyze_countries(artists)
            
            festival_data[name] = {
                'total_artists': len(artists),
                'gender': gender_counts,
                'gender_total': gender_total,
                'poc': poc_counts,
                'ratings': rating_counts,
                'countries': country_counts,
                'color': info['color'],
                'slug': info['slug']
            }
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Festival Comparison Charts - Frank's LineupRadar</title>
    <meta name="description" content="Compare lineup diversity and quality across Down The Rabbit Hole, Pinkpop, and Rock Werchter festivals.">
    <link rel="icon" type="image/png" sizes="16x16" href="shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="shared/favicon_180x180.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="shared/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        .chart-container {{
            position: relative;
            margin: 30px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stat-card h3 {{
            font-size: 1.2rem;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #007bff;
        }}
        
        /* Heatmap styles */
        .heatmap-container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 30px 0;
        }}
        
        .heatmap-header {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .heatmap-header:hover {{
            fill: #007bff;
        }}
        
        .heatmap-header.active {{
            fill: #007bff;
            font-weight: bold;
        }}
        
        .heatmap-header-rect {{
            cursor: pointer;
            transition: fill 0.2s;
        }}
        
        .heatmap-header-rect:hover {{
            fill: #e9ecef;
        }}
        
        .heatmap-header-rect.active {{
            fill: #d0e7ff;
        }}
        
        .heatmap-cell {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .heatmap-cell:hover {{
            opacity: 0.8;
            stroke: #333;
            stroke-width: 2px;
        }}
        
        .heatmap-tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 4px;
            pointer-events: none;
            font-size: 14px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        
        .heatmap-tooltip.show {{
            opacity: 1;
        }}
        
        @media (max-width: 768px) {{
            .chart-wrapper {{
                height: 300px;
            }}
            
            .heatmap-container {{
                padding: 15px;
                overflow-x: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <header class="artist-header">
            <div class="hamburger-menu">
                <button id="hamburgerBtn" class="btn btn-outline-light hamburger-btn" title="Menu">
                    <i class="bi bi-list"></i>
                </button>
                <div id="dropdownMenu" class="dropdown-menu-custom">
                    <a href="index.html" class="home-link">
                        <i class="bi bi-house-door-fill"></i> Home
                    </a>
                    {generate_hamburger_menu(path_prefix="", escaped=False)}
                </div>
            </div>
            <div class="artist-header-content">
                <h1>Festival Comparison Charts</h1>
                <p class="subtitle">Comparing lineup diversity and quality across festivals</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="artist-content container-fluid">
            <div class="row justify-content-center">
                <div class="col-12" style="max-width: 1400px;">
                    <div class="section">
"""
    
    # Calculate diversity scores for summary
    diversity_scores = {}
    for name, data in festival_data.items():
        female_count = data['gender'].get('Female', 0)
        female_pct = (female_count / data['gender_total'] * 100) if data['gender_total'] > 0 else 0
        poc_yes = data['poc'].get('Yes', 0)
        poc_pct = (poc_yes / data['total_artists'] * 100) if data['total_artists'] > 0 else 0
        
        # Count countries outside top 3 (USA, UK, and one more)
        countries = list(data['countries'].items())
        countries.sort(key=lambda x: x[1], reverse=True)
        top_3_count = sum(count for _, count in countries[:3])
        other_countries_count = data['total_artists'] - top_3_count
        other_countries_pct = (other_countries_count / data['total_artists'] * 100) if data['total_artists'] > 0 else 0
        
        # Calculate diversity index (0-100 scale)
        # 50% female = 50 points, 25% POC = 30 points, 50% outside top 3 = 20 points
        # Scale: targets reflect realistic diversity goals
        female_score = min((female_pct / 50) * 50, 50)
        poc_score = min((poc_pct / 25) * 30, 30)
        geo_score = min((other_countries_pct / 50) * 20, 20)
        diversity_index = female_score + poc_score + geo_score
        
        diversity_scores[name] = {
            'female_pct': female_pct,
            'poc_pct': poc_pct,
            'other_countries_pct': other_countries_pct,
            'diversity_index': diversity_index
        }
    
    # Sort festivals by diversity index
    sorted_festivals = sorted(diversity_scores.items(), key=lambda x: x[1]['diversity_index'], reverse=True)
    
    html += """
            <!-- Diversity Index Summary -->
            <div class="chart-container" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 30px;">
                <h2 style="color: white; margin-bottom: 20px;">Diversity Index Summary</h2>
                <p style="opacity: 0.95; margin-bottom: 25px;">Overall diversity score (0-100). Targets: 50% female (50 pts), 25% POC (30 pts), 50% from countries outside top 3 (20 pts).</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
"""
    
    for name, scores in sorted_festivals:
        html += f"""
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <h3 style="color: white; margin-bottom: 10px;">{name} 2026</h3>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700; margin: 15px 0;">{scores['diversity_index']:.1f}</div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            <div>♀️ Female: {scores['female_pct']:.1f}%</div>
                            <div>🌍 POC: {scores['poc_pct']:.1f}%</div>
                            <div>🗺️ Geographic: {scores['other_countries_pct']:.1f}%</div>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <!-- Interactive Heatmap Matrix -->
            <div class="heatmap-container">
                <h2>Festival Comparison Matrix</h2>
                <p style="color: #666; margin-bottom: 15px;">Interactive heatmap showing relative strength across metrics. Darker colors indicate higher values. Click column headers to sort, hover cells for exact values.</p>
                
                <!-- Legend -->
                <div style="display: flex; gap: 20px; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; flex-wrap: wrap; font-size: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 40px; height: 20px; background: linear-gradient(to right, #f0f0f0, #4CAF50); border: 1px solid #ddd; border-radius: 3px;"></div>
                        <span>Avg Rating (0-10)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 40px; height: 20px; background: linear-gradient(to right, #f0f0f0, #9C27B0); border: 1px solid #ddd; border-radius: 3px;"></div>
                        <span>Female % (0-50%)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 40px; height: 20px; background: linear-gradient(to right, #f0f0f0, #FF9800); border: 1px solid #ddd; border-radius: 3px;"></div>
                        <span>POC % (0-25%)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 40px; height: 20px; background: linear-gradient(to right, #f0f0f0, #2196F3); border: 1px solid #ddd; border-radius: 3px;"></div>
                        <span>Geographic % (0-50%)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 40px; height: 20px; background: linear-gradient(to right, #f0f0f0, #E91E63); border: 1px solid #ddd; border-radius: 3px;"></div>
                        <span>Diversity Score (0-100)</span>
                    </div>
                </div>
                
                <div id="heatmap"></div>
            </div>
            <div class="heatmap-tooltip" id="heatmapTooltip"></div>
            
            <!-- Overview Stats -->
            <div class="stats-grid">
"""
    
    for name, data in festival_data.items():
        female_count = data['gender'].get('Female', 0)
        female_pct = (female_count / data['gender_total'] * 100) if data['gender_total'] > 0 else 0
        poc_yes = data['poc'].get('Yes', 0)
        poc_pct = (poc_yes / data['total_artists'] * 100) if data['total_artists'] > 0 else 0
        avg_rating = sum(rating * count for rating, count in data['ratings'].items()) / sum(data['ratings'].values()) if data['ratings'] else 0
        
        html += f"""
                <div class="stat-card">
                    <h3>{name} 2026</h3>
                    <div class="stat-value">{data['total_artists']}</div>
                    <div>Total Artists</div>
                    <hr>
                    <div><strong>{female_pct:.1f}%</strong> Female Front Person</div>
                    <div><strong>{poc_pct:.1f}%</strong> POC Front Person</div>
                    <div><strong>{avg_rating:.1f}</strong> Average Rating</div>
                </div>
"""
    
    html += """
            </div>
            
            <!-- Gender Distribution Chart -->
            <div class="chart-container">
                <h2>Gender Distribution of Front Person</h2>
                <div class="chart-wrapper">
                    <canvas id="genderChart"></canvas>
                </div>
            </div>
            
            <!-- POC Representation Chart -->
            <div class="chart-container">
                <h2>Person of Color Representation</h2>
                <div class="chart-wrapper">
                    <canvas id="pocChart"></canvas>
                </div>
            </div>
            
            <!-- Rating Distribution Charts -->
            <div class="chart-container">
                <h2>Rating Distribution by Festival</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 20px;">
                    <div style="text-align: center;">
                        <h3 style="margin-bottom: 15px;">Down The Rabbit Hole</h3>
                        <div style="height: 300px;"><canvas id="ratingsDTRH"></canvas></div>
                    </div>
                    <div style="text-align: center;">
                        <h3 style="margin-bottom: 15px;">Pinkpop</h3>
                        <div style="height: 300px;"><canvas id="ratingsPinkpop"></canvas></div>
                    </div>
                    <div style="text-align: center;">
                        <h3 style="margin-bottom: 15px;">Rock Werchter</h3>
                        <div style="height: 300px;"><canvas id="ratingsRockWerchter"></canvas></div>
                    </div>
                    <div style="text-align: center;">
                        <h3 style="margin-bottom: 15px;">Footprints</h3>
                        <div style="height: 300px;"><canvas id="ratingsFootprints"></canvas></div>
                    </div>
                </div>
            </div>
            
            <!-- Country Distribution -->
            <div class="chart-container">
                <h2>Country Distribution</h2>
                <p>Geographic representation of artists across festivals (top countries shown).</p>
                <div class="chart-wrapper">
                    <canvas id="countryChart"></canvas>
                </div>
            </div>
            
            <!-- Combined Diversity Score -->
            <div class="chart-container">
                <h2>Female & Person of Color Representation Combined</h2>
                <div class="chart-wrapper">
                    <canvas id="diversityChart"></canvas>
                </div>
            </div>
            
        </div>
    </div>
    
    <script>
        // Prepare data
        const festivalData = """ + json.dumps(festival_data, indent=8) + """;
        
        // Prepare heatmap data
        const heatmapData = [];
        const metrics = ['avgRating', 'female', 'poc', 'geographic', 'diversity'];
        const metricLabels = ['Avg Rating', 'Female %', 'POC %', 'Geographic %', 'Diversity Score'];
        const metricTooltips = {
            avgRating: 'Average rating across all artists (0-10 scale)',
            female: 'Percentage of artists with female front person',
            poc: 'Percentage of artists with Person of Color as front person',
            geographic: 'Percentage of artists from countries outside top 3 (geographic diversity)',
            diversity: 'Overall diversity score combining gender, POC, and geographic diversity (0-100 scale)'
        };
        
        for (const [festival, data] of Object.entries(festivalData)) {
            const femaleCount = data.gender['Female'] || 0;
            const femalePct = data.gender_total > 0 ? (femaleCount / data.gender_total * 100) : 0;
            const pocYes = data.poc['Yes'] || 0;
            const pocPct = data.total_artists > 0 ? (pocYes / data.total_artists * 100) : 0;
            
            // Calculate average rating
            let totalRating = 0;
            let totalCount = 0;
            for (const [rating, count] of Object.entries(data.ratings)) {
                totalRating += parseFloat(rating) * count;
                totalCount += count;
            }
            const avgRating = totalCount > 0 ? totalRating / totalCount : 0;
            
            // Calculate geographic diversity
            const countries = Object.entries(data.countries).sort((a, b) => b[1] - a[1]);
            const top3Count = countries.slice(0, 3).reduce((sum, [_, count]) => sum + count, 0);
            const otherCountriesCount = data.total_artists - top3Count;
            const geographicPct = data.total_artists > 0 ? (otherCountriesCount / data.total_artists * 100) : 0;
            
            // Calculate diversity index
            const femaleScore = Math.min((femalePct / 50) * 50, 50);
            const pocScore = Math.min((pocPct / 25) * 30, 30);
            const geoScore = Math.min((geographicPct / 50) * 20, 20);
            const diversityIndex = femaleScore + pocScore + geoScore;
            
            heatmapData.push({
                festival: festival,
                avgRating: avgRating,
                female: femalePct,
                poc: pocPct,
                geographic: geographicPct,
                diversity: diversityIndex,
                color: data.color
            });
        }
        
        // Render heatmap
        function renderHeatmap(sortBy = 'diversity') {
            // Sort data
            const sortedData = [...heatmapData].sort((a, b) => b[sortBy] - a[sortBy]);
            
            // Clear existing
            d3.select('#heatmap').selectAll('*').remove();
            
            // Dimensions
            const margin = {top: 10, right: 40, bottom: 40, left: 20};
            const festivalColWidth = 200;
            const cellWidth = 100;
            const cellHeight = 50;
            const headerHeight = 40;
            const width = festivalColWidth + metrics.length * cellWidth + margin.left + margin.right;
            const height = headerHeight + sortedData.length * cellHeight + margin.top + margin.bottom;
            
            // Create SVG
            const svg = d3.select('#heatmap')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            const g = svg.append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);
            
            // Create color scales for each metric
            const colorScales = {
                avgRating: d3.scaleLinear().domain([0, 10]).range(['#f0f0f0', '#4CAF50']),
                female: d3.scaleLinear().domain([0, 50]).range(['#f0f0f0', '#9C27B0']),
                poc: d3.scaleLinear().domain([0, 25]).range(['#f0f0f0', '#FF9800']),
                geographic: d3.scaleLinear().domain([0, 50]).range(['#f0f0f0', '#2196F3']),
                diversity: d3.scaleLinear().domain([0, 100]).range(['#f0f0f0', '#E91E63'])
            };
            
            // Add header row background for "Festival" column
            g.append('rect')
                .attr('x', 0)
                .attr('y', 0)
                .attr('width', festivalColWidth)
                .attr('height', headerHeight)
                .attr('fill', '#f8f9fa')
                .attr('stroke', '#ddd')
                .attr('stroke-width', 2);
            
            // Add "Festival" header text
            g.append('text')
                .attr('x', festivalColWidth / 2)
                .attr('y', headerHeight / 2)
                .attr('text-anchor', 'middle')
                .attr('alignment-baseline', 'middle')
                .attr('font-weight', 'bold')
                .attr('font-size', '14px')
                .text('Festival');
            
            // Add column headers for metrics (clickable)
            metrics.forEach((metric, i) => {
                const headerGroup = g.append('g')
                    .style('cursor', 'pointer')
                    .on('click', () => renderHeatmap(metric));
                
                // Add tooltip
                headerGroup.append('title')
                    .text(metricTooltips[metric]);
                
                // Header background
                headerGroup.append('rect')
                    .attr('class', `heatmap-header-rect $${sortBy === metric ? 'active' : ''}`)
                    .attr('x', festivalColWidth + i * cellWidth)
                    .attr('y', 0)
                    .attr('width', cellWidth)
                    .attr('height', headerHeight)
                    .attr('fill', sortBy === metric ? '#d0e7ff' : '#f8f9fa')
                    .attr('stroke', '#ddd')
                    .attr('stroke-width', 2);
                
                // Header text
                headerGroup.append('text')
                    .attr('class', `heatmap-header $${sortBy === metric ? 'active' : ''}`)
                    .attr('x', festivalColWidth + i * cellWidth + cellWidth / 2)
                    .attr('y', headerHeight / 2)
                    .attr('text-anchor', 'middle')
                    .attr('alignment-baseline', 'middle')
                    .attr('font-weight', sortBy === metric ? 'bold' : 'bold')
                    .attr('font-size', '13px')
                    .attr('fill', sortBy === metric ? '#007bff' : '#333')
                    .text(metricLabels[i]);
                
                // Sort indicator
                if (sortBy === metric) {
                    headerGroup.append('text')
                        .attr('x', festivalColWidth + i * cellWidth + cellWidth / 2)
                        .attr('y', headerHeight / 2 + 14)
                        .attr('text-anchor', 'middle')
                        .attr('font-size', '10px')
                        .attr('fill', '#007bff')
                        .text('▼');
                }
            });
            
            // Add cells
            const tooltip = d3.select('#heatmapTooltip');
            
            sortedData.forEach((row, rowIndex) => {
                // Add festival name cell (first column)
                const festivalCell = g.append('rect')
                    .attr('x', 0)
                    .attr('y', headerHeight + rowIndex * cellHeight)
                    .attr('width', festivalColWidth)
                    .attr('height', cellHeight)
                    .attr('fill', '#f8f9fa')
                    .attr('stroke', '#ddd')
                    .attr('stroke-width', 1);
                
                g.append('text')
                    .attr('x', festivalColWidth / 2)
                    .attr('y', headerHeight + rowIndex * cellHeight + cellHeight / 2)
                    .attr('text-anchor', 'middle')
                    .attr('alignment-baseline', 'middle')
                    .attr('font-size', '13px')
                    .attr('font-weight', '500')
                    .attr('pointer-events', 'none')
                    .text(row.festival + ' 2026');
                
                // Add metric cells
                metrics.forEach((metric, colIndex) => {
                    const value = row[metric];
                    const cell = g.append('rect')
                        .attr('class', 'heatmap-cell')
                        .attr('x', festivalColWidth + colIndex * cellWidth)
                        .attr('y', headerHeight + rowIndex * cellHeight)
                        .attr('width', cellWidth)
                        .attr('height', cellHeight)
                        .attr('fill', colorScales[metric](value))
                        .attr('stroke', '#ddd')
                        .attr('stroke-width', 1);
                    
                    // Add value text
                    g.append('text')
                        .attr('x', festivalColWidth + colIndex * cellWidth + cellWidth / 2)
                        .attr('y', headerHeight + rowIndex * cellHeight + cellHeight / 2)
                        .attr('text-anchor', 'middle')
                        .attr('alignment-baseline', 'middle')
                        .attr('font-size', '12px')
                        .attr('font-weight', 'bold')
                        .attr('pointer-events', 'none')
                        .text(value.toFixed(1));
                    
                    // Tooltip
                    cell.on('mouseover', function(event) {
                        tooltip
                            .style('left', (event.pageX + 10) + 'px')
                            .style('top', (event.pageY - 10) + 'px')
                            .html(`<strong>${row.festival}</strong><br>${metricLabels[colIndex]}: ${value.toFixed(2)}`)
                            .classed('show', true);
                    })
                    .on('mouseout', function() {
                        tooltip.classed('show', false);
                    });
                });
            });
        }
        
        // Initial render
        renderHeatmap('diversity');
        
        // Gender Distribution Chart
        const genderLabels = ['Male', 'Female', 'Mixed', 'Non-binary', 'Unknown'];
        const genderDatasets = [];
        
        for (const [festival, data] of Object.entries(festivalData)) {
            const genderData = genderLabels.map(label => data.gender[label] || 0);
            genderDatasets.push({
                label: festival + ' 2026',
                data: genderData,
                backgroundColor: data.color,
                borderColor: data.color,
                borderWidth: 1
            });
        }
        
        new Chart(document.getElementById('genderChart'), {
            type: 'bar',
            data: {
                labels: genderLabels,
                datasets: genderDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        
        // POC Representation Chart
        const pocLabels = ['Yes', 'No', 'Unknown'];
        const pocDatasets = [];
        
        for (const [festival, data] of Object.entries(festivalData)) {
            const pocData = pocLabels.map(label => data.poc[label] || 0);
            pocDatasets.push({
                label: festival + ' 2026',
                data: pocData,
                backgroundColor: data.color,
                borderColor: data.color,
                borderWidth: 1
            });
        }
        
        new Chart(document.getElementById('pocChart'), {
            type: 'bar',
            data: {
                labels: pocLabels,
                datasets: pocDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        
        // Rating Distribution Bar Charts
        const ratingLabels = ['5', '6', '7', '8', '9'];
        
        // Down The Rabbit Hole
        const dtrh = festivalData['Down The Rabbit Hole'];
        const dtrhRatings = ratingLabels.map(label => dtrh.ratings[parseInt(label)] || 0);
        new Chart(document.getElementById('ratingsDTRH'), {
            type: 'bar',
            data: {
                labels: ratingLabels.map(l => `Rating ${l}`),
                datasets: [{
                    label: 'Number of Artists',
                    data: dtrhRatings,
                    backgroundColor: '#FF6B6B',
                    borderColor: '#FF6B6B',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Artists'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Rating'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Pinkpop
        const pinkpop = festivalData['Pinkpop'];
        const pinkpopRatings = ratingLabels.map(label => pinkpop.ratings[parseInt(label)] || 0);
        new Chart(document.getElementById('ratingsPinkpop'), {
            type: 'bar',
            data: {
                labels: ratingLabels.map(l => `Rating ${l}`),
                datasets: [{
                    label: 'Number of Artists',
                    data: pinkpopRatings,
                    backgroundColor: '#4ECDC4',
                    borderColor: '#4ECDC4',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Artists'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Rating'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Rock Werchter
        const rockWerchter = festivalData['Rock Werchter'];
        const rockWerchterRatings = ratingLabels.map(label => rockWerchter.ratings[parseInt(label)] || 0);
        new Chart(document.getElementById('ratingsRockWerchter'), {
            type: 'bar',
            data: {
                labels: ratingLabels.map(l => `Rating ${l}`),
                datasets: [{
                    label: 'Number of Artists',
                    data: rockWerchterRatings,
                    backgroundColor: '#95E1D3',
                    borderColor: '#95E1D3',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Artists'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Rating'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Footprints
        const footprints = festivalData['Footprints'];
        const footprintsRatings = ratingLabels.map(label => footprints.ratings[parseInt(label)] || 0);
        new Chart(document.getElementById('ratingsFootprints'), {
            type: 'bar',
            data: {
                labels: ratingLabels.map(l => `Rating ${l}`),
                datasets: [{
                    label: 'Number of Artists',
                    data: footprintsRatings,
                    backgroundColor: '#FFA07A',
                    borderColor: '#FFA07A',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Artists'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Rating'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Country Distribution Chart
        // Aggregate all countries across festivals
        const allCountries = {};
        for (const [festival, data] of Object.entries(festivalData)) {
            for (const [country, count] of Object.entries(data.countries)) {
                if (!allCountries[country]) {
                    allCountries[country] = {};
                }
                allCountries[country][festival] = count;
            }
        }
        
        // Sort by total count and take top 10
        const countrySums = {};
        for (const [country, festivals] of Object.entries(allCountries)) {
            countrySums[country] = Object.values(festivals).reduce((a, b) => a + b, 0);
        }
        const topCountries = Object.keys(countrySums)
            .sort((a, b) => countrySums[b] - countrySums[a])
            .slice(0, 10);
        
        // Add "Other" category for remaining countries
        const countryLabels = [...topCountries, 'Other'];
        
        const countryDatasets = [];
        for (const [festival, data] of Object.entries(festivalData)) {
            const countryData = topCountries.map(country => data.countries[country] || 0);
            
            // Calculate "Other" count
            const topCountryTotal = countryData.reduce((a, b) => a + b, 0);
            const allCountryTotal = Object.values(data.countries).reduce((a, b) => a + b, 0);
            const otherCount = allCountryTotal - topCountryTotal;
            countryData.push(otherCount);
            
            countryDatasets.push({
                label: festival + ' 2026',
                data: countryData,
                backgroundColor: data.color,
                borderColor: data.color,
                borderWidth: 1
            });
        }
        
        new Chart(document.getElementById('countryChart'), {
            type: 'bar',
            data: {
                labels: countryLabels,
                datasets: countryDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Artists'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Country'
                        }
                    }
                }
            }
        });
        
        // Diversity Score Chart (Female + POC percentages)
        const diversityDatasets = [];
        const diversityLabels = Object.keys(festivalData).map(f => f + ' 2026');
        
        const femalePercentages = [];
        const pocPercentages = [];
        
        for (const [festival, data] of Object.entries(festivalData)) {
            const femaleCount = data.gender['Female'] || 0;
            const femalePct = data.gender_total > 0 ? (femaleCount / data.gender_total * 100) : 0;
            femalePercentages.push(femalePct.toFixed(1));
            
            const pocYes = data.poc['Yes'] || 0;
            const pocPct = data.total_artists > 0 ? (pocYes / data.total_artists * 100) : 0;
            pocPercentages.push(pocPct.toFixed(1));
        }
        
        new Chart(document.getElementById('diversityChart'), {
            type: 'bar',
            data: {
                labels: diversityLabels,
                datasets: [
                    {
                        label: 'Female Front Person %',
                        data: femalePercentages,
                        backgroundColor: '#FF6B9D',
                        borderColor: '#FF6B9D',
                        borderWidth: 1
                    },
                    {
                        label: 'POC Front Person %',
                        data: pocPercentages,
                        backgroundColor: '#4ECDC4',
                        borderColor: '#4ECDC4',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    </script>
                    </div>
                </div>
            </div>
        </div>
        
        <footer style="background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em; margin-top: 40px;">
            <button class="dark-mode-toggle" id="darkModeToggle" title="Toggle dark mode">
                <i class="bi bi-moon-fill"></i>
            </button>
            <div>
                <p style="margin-bottom: 15px;">
                    <strong>Content Notice:</strong> These pages combine content scraped from festival websites 
                    with AI-generated content using <strong>Azure OpenAI GPT-4o</strong>.
                </p>
                <p style="margin-bottom: 15px;">
                    <strong>⚠️ Disclaimer:</strong> Information may be incomplete or inaccurate due to automated generation and web scraping. 
                    Please verify critical details on official sources.
                </p>
                <p style="margin-bottom: 0;">
                    Generated with ❤️ • 
                    <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff; text-decoration: none;">
                        <i class="bi bi-github"></i> View on GitHub
                    </a>
                </p>
            </div>
        </footer>
    </div>
    <script src="shared/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    # Write the HTML file
    output_path = Path('docs/charts.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated charts page: {output_path}")
    print(f"  Festivals analyzed: {len(festival_data)}")
    for name, data in festival_data.items():
        print(f"    - {name}: {data['total_artists']} artists")

if __name__ == "__main__":
    generate_charts_page()
