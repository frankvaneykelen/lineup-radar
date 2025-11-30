"""
Generate a charts page comparing festival lineups.
"""

import csv
from pathlib import Path
import json

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
        rating = artist.get('My rating', '').strip()
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
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="shared/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
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
        
        @media (max-width: 768px) {{
            .chart-wrapper {{
                height: 300px;
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
                    <div class="festival-section">Down The Rabbit Hole</div>
                    <a href="down-the-rabbit-hole/2026/index.html" class="festival-year">2026 Lineup</a>
                    <div class="festival-section">Pinkpop</div>
                    <a href="pinkpop/2026/index.html" class="festival-year">2026 Lineup</a>
                    <div class="festival-section">Rock Werchter</div>
                    <a href="rock-werchter/2026/index.html" class="festival-year">2026 Lineup</a>
                    <div class="festival-section">About</div>
                    <a href="charts.html" class="festival-year">
                        <i class="bi bi-bar-chart-fill"></i> Charts
                    </a>
                    <a href="faq.html" class="festival-year">
                        <i class="bi bi-question-circle"></i> FAQ
                    </a>
                </div>
            </div>
            <div class="artist-header-content">
                <h1>Festival Comparison Charts</h1>
                <p class="subtitle">Comparing lineup diversity and quality across festivals</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="container" style="max-width: 1200px;">
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
    
    <script src="shared/script.js"></script>
    <script>
        // Prepare data
        const festivalData = """ + json.dumps(festival_data, indent=8) + """;
        
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
