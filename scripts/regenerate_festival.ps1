#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regenerate HTML pages for a single festival
.DESCRIPTION
    This script regenerates lineup index page, about page, and individual artist pages 
    for a single specified festival and year. It runs generate_html.py, generate_about.py,
    and generate_artist_pages.py for the specified festival/year combination.
    
.PARAMETER Festival
    Required festival slug. Must be one of: best-kept-secret, down-the-rabbit-hole, pinkpop, rock-werchter, footprints

.PARAMETER Year
    Optional year (default: 2026)

.PARAMETER IncludePlaylist
    Optional switch to include Spotify playlist generation (skipped by default)

.EXAMPLE
    .\regenerate_festival.ps1 -Festival down-the-rabbit-hole
    Regenerates all pages for Down The Rabbit Hole 2026.

.EXAMPLE
    .\regenerate_festival.ps1 -Festival pinkpop -Year 2025
    Regenerates all pages for Pinkpop 2025.

.EXAMPLE
    .\regenerate_festival.ps1 -Festival pinkpop -Year 2025 -IncludePlaylist
    Regenerates all pages for Pinkpop 2025 including Spotify playlist.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Festival,
    
    [int]$Year = 2026,
    
    [switch]$IncludePlaylist
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Set console output encoding to UTF-8 to handle Unicode characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regenerating Festival HTML Pages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Festival: $Festival" -ForegroundColor White
Write-Host "Year: $Year" -ForegroundColor White
Write-Host ""

# Load Spotify credentials from .keys.txt
$spotifyClientId = ""
$spotifyClientSecret = ""

if ($IncludePlaylist) {
    Write-Host "Loading Spotify credentials..." -ForegroundColor Gray
    
    if (Test-Path ".keys.txt") {
        Get-Content ".keys.txt" | ForEach-Object {
            # Support KEY=value format
            if ($_ -match "^SPOTIFY_CLIENT_ID=(.+)$") {
                $spotifyClientId = $matches[1]
            }
            if ($_ -match "^SPOTIFY_CLIENT_SECRET=(.+)$") {
                $spotifyClientSecret = $matches[1]
            }
            # Support PowerShell variable assignment format
            if ($_ -match '\$env:SPOTIFY_CLIENT_ID\s*=\s*"([^"]+)"') {
                $spotifyClientId = $matches[1]
            }
            if ($_ -match '\$env:SPOTIFY_CLIENT_SECRET\s*=\s*"([^"]+)"') {
                $spotifyClientSecret = $matches[1]
            }
        }
        
        if ($spotifyClientId -and $spotifyClientSecret) {
            Write-Host "✓ Spotify credentials loaded" -ForegroundColor Green
        } else {
            Write-Host "⚠ Spotify credentials not found in .keys.txt - playlist generation will be skipped" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ .keys.txt not found - playlist generation will be skipped" -ForegroundColor Yellow
    }
}
Write-Host ""

# Get festival display name from config
$getFestivalNameScript = @"
import sys
sys.path.insert(0, 'scripts')
from helpers.config import FESTIVALS
festival = '$Festival'
if festival in FESTIVALS:
    print(FESTIVALS[festival].get('name', festival))
else:
    print(festival)
"@

$festivalName = python -c $getFestivalNameScript
if (-not $festivalName -or $LASTEXITCODE -ne 0) {
    $festivalName = $Festival
}

# Track success/failure
# Base operations: lineup + about + artist pages
# Optional: timetable (if schedule data exists) + playlist (if requested)
# We'll update totalOperations as we discover what's needed
$totalOperations = 3  # lineup + about + artist pages (will add timetable + playlist if applicable)
$currentOperation = 0
$successCount = 0
$failureCount = 0
$startTime = Get-Date

# Check for schedule data to determine if we should generate timetable
$csvPath = "docs/$Festival/$Year/$Year.csv"
$hasScheduleDataCheck = $false
if (Test-Path $csvPath) {
    $csvContent = Get-Content $csvPath -Raw -Encoding UTF8
    if ($csvContent -match "Date,Start Time,End Time,Stage" -or $csvContent -match "Date" -and $csvContent -match "Start Time") {
        $hasScheduleDataCheck = $true
        $totalOperations++
    }
}

# Add playlist to count if requested
if ($IncludePlaylist) {
    $totalOperations++
}

Write-Host "Processing: $festivalName $Year..." -ForegroundColor Yellow
Write-Host ""

try {
    # 1. Run the lineup index page generation script
    $currentOperation++
    Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating lineup index ($currentOperation of $totalOperations)" -PercentComplete (($currentOperation / $totalOperations) * 100)
    
    $command1 = "python scripts/generate_html.py --festival $Festival --year $Year"
    Write-Host "Running: $command1" -ForegroundColor Gray
    
    $output1 = & python scripts/generate_html.py --festival $Festival --year $Year 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to generate lineup index" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output1 -ForegroundColor Red
        $failureCount++
    } else {
        Write-Host "✓ Generated lineup index page" -ForegroundColor Green
        # Extract and log the saved file path
        $matchedLine = $output1 | Where-Object { $_ -match "✓ Generated (.+)" } | Select-Object -First 1
        if ($matchedLine -and $matchedLine -match "✓ Generated (.+)") {
            Write-Host "  → $($matches[1])" -ForegroundColor DarkGray
        }
        $successCount++
    }
    
    # 2. Generate timetable if schedule data exists
    $csvPath = "docs/$Festival/$Year/$Year.csv"
    $hasScheduleData = $false
    if (Test-Path $csvPath) {
        $csvContent = Get-Content $csvPath -Raw -Encoding UTF8
        if ($csvContent -match "Date,Start Time,End Time,Stage" -or $csvContent -match "Date" -and $csvContent -match "Start Time") {
            $hasScheduleData = $true
        }
    }
    
    if ($hasScheduleData) {
        $currentOperation++
        Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating timetable ($currentOperation of $totalOperations)" -PercentComplete (($currentOperation / $totalOperations) * 100)
        
        $commandTimetable = "python scripts/generate_timetable.py --festival $Festival --year $Year"
        Write-Host "Running: $commandTimetable" -ForegroundColor Gray
        
        $outputTimetable = & python scripts/generate_timetable.py --festival $Festival --year $Year 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Generated timetable" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "⚠ Failed to generate timetable (skipping)" -ForegroundColor Yellow
            Write-Host "Error output:" -ForegroundColor Yellow
            Write-Host $outputTimetable -ForegroundColor Yellow
            # Don't count as failure since timetable is optional
        }
    } else {
        Write-Host "⊘ Skipping timetable (no schedule data)" -ForegroundColor DarkGray
    }
    
    # 3. Run the about page generation script
    $currentOperation++
    Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating about page ($currentOperation of $totalOperations)" -PercentComplete (($currentOperation / $totalOperations) * 100)
    
    $commandAbout = "python scripts/generate_about.py --festival $Festival --year $Year --ai"
    Write-Host "Running: $commandAbout" -ForegroundColor Gray
    
    $outputAbout = & python scripts/generate_about.py --festival $Festival --year $Year --ai 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Generated about page" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "✗ Failed to generate about page" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $outputAbout -ForegroundColor Red
        $failureCount++
    }
    
    # 4. Run the artist pages generation script
    $currentOperation++
    Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating artist pages ($currentOperation of $totalOperations)" -PercentComplete (($currentOperation / $totalOperations) * 100)
    
    $command2 = "python scripts/generate_artist_pages.py --festival $Festival --year $Year"
    Write-Host "Running: $command2" -ForegroundColor Gray
    
    $output2 = & python scripts/generate_artist_pages.py --festival $Festival --year $Year 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Generated artist pages" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "✗ Failed to generate artist pages" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output2 -ForegroundColor Red
        $failureCount++
    }
    
    # 5. Generate/update Spotify playlist if requested and credentials are available
    if ($IncludePlaylist) {
        $currentOperation++
        Write-Progress -Activity "Regenerating Festival Pages" -Status "Updating Spotify playlist ($currentOperation of $totalOperations)" -PercentComplete (($currentOperation / $totalOperations) * 100)
        
        if ($spotifyClientId -and $spotifyClientSecret) {
            $env:SPOTIFY_CLIENT_ID = $spotifyClientId
            $env:SPOTIFY_CLIENT_SECRET = $spotifyClientSecret
            
            $command3 = "python scripts/generate_spotify_playlists.py --festival $Festival --year $Year"
            Write-Host "Running: $command3" -ForegroundColor Gray
            Write-Host ""
            
            # Execute interactively (allows user input for missing Spotify links)
            & python scripts/generate_spotify_playlists.py --festival $Festival --year $Year
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "✓ Updated Spotify playlist" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host ""
                Write-Host "⚠ Failed to update Spotify playlist" -ForegroundColor Yellow
                $failureCount++
            }
        } else {
            Write-Host "⊘ Skipping Spotify playlist (no credentials)" -ForegroundColor DarkGray
            # Still count as successful since it's optional
            $successCount++
        }
    }
}
catch {
    Write-Host "✗ Exception while processing $festivalName $Year" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

# Complete progress bar
Write-Progress -Activity "Regenerating Festival Pages" -Status "Complete" -Completed

# Calculate duration
$endTime = Get-Date
$duration = $endTime - $startTime
$hours = [math]::Floor($duration.TotalHours)
$minutes = $duration.Minutes
$seconds = $duration.Seconds
$durationFormatted = "{0:D2}:{1:D2}:{2:D2}" -f [int]$hours, [int]$minutes, [int]$seconds

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regeneration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Festival: $festivalName $Year" -ForegroundColor White
$operationsList = if ($IncludePlaylist) { "lineup + about + artist pages + playlist" } else { "lineup + about + artist pages" }
Write-Host "Operations: $operationsList" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $durationFormatted" -ForegroundColor Gray
Write-Host ""

# Exit with appropriate code
if ($failureCount -eq 0) {
    Write-Host "✓ All pages regenerated successfully for $festivalName!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some operations failed. Check errors above." -ForegroundColor Red
    exit 1
}
