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

.EXAMPLE
    .\regenerate_festival.ps1 -Festival down-the-rabbit-hole
    Regenerates all pages for Down The Rabbit Hole 2026.

.EXAMPLE
    .\regenerate_festival.ps1 -Festival pinkpop -Year 2025
    Regenerates all pages for Pinkpop 2025.
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('alkmaarse-eigenste', 'best-kept-secret', 'down-the-rabbit-hole', 'pinkpop', 'rock-werchter', 'footprints')]
    [string]$Festival,
    
    [int]$Year = 2026
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Set console output encoding to UTF-8 to handle Unicode characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Festival name mapping
$festivalNames = @{
    'alkmaarse-eigenste' = 'Alkmaarse Eigenste'
    'best-kept-secret' = 'Best Kept Secret'
    'down-the-rabbit-hole' = 'Down The Rabbit Hole'
    'pinkpop' = 'Pinkpop'
    'rock-werchter' = 'Rock Werchter'
    'footprints' = 'Footprints'
}

$festivalName = $festivalNames[$Festival]

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regenerating Festival HTML Pages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Festival: $festivalName" -ForegroundColor White
Write-Host "Year: $Year" -ForegroundColor White
Write-Host ""

# Load Spotify credentials from .keys.txt
Write-Host "Loading Spotify credentials..." -ForegroundColor Gray
$spotifyClientId = ""
$spotifyClientSecret = ""

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

Write-Host ""

# Track success/failure
$totalOperations = 4  # lineup + about + artist pages + playlist
$currentOperation = 0
$successCount = 0
$failureCount = 0
$startTime = Get-Date

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
        $successCount++
    }
    
    # 2. Run the about page generation script
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
    
    # 3. Run the artist pages generation script
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
    
    # 4. Generate/update Spotify playlist if credentials are available
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
$durationFormatted = "{0:D2}:{1:D2}:{2:D2}" -f $hours, $minutes, $seconds

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regeneration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Festival: $festivalName $Year" -ForegroundColor White
Write-Host "Operations: lineup + about + artist pages + playlist" -ForegroundColor White
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
