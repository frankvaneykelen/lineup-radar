#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regenerate all HTML pages for all festivals and years
.DESCRIPTION
    This script regenerates both lineup index pages and individual artist pages 
    for all configured festivals and years. It runs generate_html.py followed by 
    generate_artist_pages.py for each festival/year combination.

.PARAMETER SkipPlaylists
    Skip Spotify playlist generation

.EXAMPLE
    .\regenerate_all.ps1
    Regenerates all pages for all festivals.

.EXAMPLE
    .\regenerate_all.ps1 -SkipPlaylists
    Regenerates all pages but skips Spotify playlist generation.
#>

param(
    [switch]$SkipPlaylists
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Set console output encoding to UTF-8 to handle Unicode characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regenerating All Festival HTML Pages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define festival configurations
$allFestivals = @(
    [PSCustomObject]@{
        Name = "Down The Rabbit Hole"
        Slug = "down-the-rabbit-hole"
        Year = 2026
    },
    [PSCustomObject]@{
        Name = "Pinkpop"
        Slug = "pinkpop"
        Year = 2026
    },
    [PSCustomObject]@{
        Name = "Rock Werchter"
        Slug = "rock-werchter"
        Year = 2026
    },
    [PSCustomObject]@{
        Name = "Footprints"
        Slug = "footprints"
        Year = 2026
    },
    [PSCustomObject]@{
        Name = "Best Kept Secret"
        Slug = "best-kept-secret"
        Year = 2026
    }
)

$festivalsToProcess = $allFestivals

# Load Spotify credentials from .keys.txt (unless skipping playlists)
$spotifyClientId = ""
$spotifyClientSecret = ""

if (-not $SkipPlaylists) {
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
} else {
    Write-Host "⊘ Skipping Spotify playlist generation (--SkipPlaylists flag)" -ForegroundColor DarkGray
}

Write-Host ""

# Track success/failure and calculate operations
$totalFestivals = $festivalsToProcess.Count
$operationsPerFestival = if ($SkipPlaylists) { 3 } else { 4 }  # Each festival: lineup + about + artist pages (+ playlist if not skipping)
$totalOperations = ($totalFestivals * $operationsPerFestival) + 3  # Plus homepage + charts + FAQ
$currentOperation = 0
$successCount = 0
$failureCount = 0
$startTime = Get-Date

# Process each festival
foreach ($festival in $festivalsToProcess) {
    $festivalName = $festival.Name
    $festivalSlug = $festival.Slug
    $year = $festival.Year
    
    $currentOperation++
    $percentComplete = [int](($currentOperation / $totalOperations) * 100)
    Write-Progress -Activity "Regenerating Festival Pages" -Status "Processing $festivalName $year ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
    
    Write-Host "Processing: $festivalName $year..." -ForegroundColor Yellow
    Write-Host "Festival slug: $festivalSlug" -ForegroundColor Gray
    Write-Host ""
    
    try {
        # Run the lineup index page generation script
        $command1 = "python scripts/generate_html.py --festival $festivalSlug --year $year"
        Write-Host "Running: $command1" -ForegroundColor Gray
        
        # Execute and capture output
        $output1 = & python scripts/generate_html.py --festival $festivalSlug --year $year 2>&1
        
        # Check if command succeeded
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Failed to generate lineup index for $festivalName $year" -ForegroundColor Red
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $output1 -ForegroundColor Red
            $failureCount++
            continue
        }
        
        Write-Host "✓ Generated lineup index page" -ForegroundColor Green
        $successCount++
        
        # Update progress for about page
        $currentOperation++
        $percentComplete = [int](($currentOperation / $totalOperations) * 100)
        Write-Progress -Activity "Regenerating Festival Pages" -Status "Processing $festivalName about page ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
        
        # Run the about page generation script
        $commandAbout = "python scripts/generate_about.py --festival $festivalSlug --year $year --ai"
        Write-Host "Running: $commandAbout" -ForegroundColor Gray
        
        # Execute and capture output
        $outputAbout = & python scripts/generate_about.py --festival $festivalSlug --year $year --ai 2>&1
        
        # Check if command succeeded
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Generated about page" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Failed to generate about page for $festivalName $year" -ForegroundColor Red
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $outputAbout -ForegroundColor Red
            $failureCount++
        }
        
        # Update progress for artist pages
        $currentOperation++
        $percentComplete = [int](($currentOperation / $totalOperations) * 100)
        Write-Progress -Activity "Regenerating Festival Pages" -Status "Processing $festivalName artist pages ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
        
        # Run the artist pages generation script
        $command2 = "python scripts/generate_artist_pages.py --festival $festivalSlug --year $year"
        Write-Host "Running: $command2" -ForegroundColor Gray
        
        # Execute and capture output
        $output2 = & python scripts/generate_artist_pages.py --festival $festivalSlug --year $year 2>&1
        
        # Check if command succeeded
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Generated artist pages" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Failed to generate artist pages for $festivalName $year" -ForegroundColor Red
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $output2 -ForegroundColor Red
            $failureCount++
        }
        
        # Generate/update Spotify playlist if not skipped and credentials are available
        if (-not $SkipPlaylists) {
            # Update progress for Spotify playlist
            $currentOperation++
            $percentComplete = [int](($currentOperation / $totalOperations) * 100)
            Write-Progress -Activity "Regenerating Festival Pages" -Status "Updating Spotify playlist for $festivalName ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
            
            if ($spotifyClientId -and $spotifyClientSecret) {
                $env:SPOTIFY_CLIENT_ID = $spotifyClientId
                $env:SPOTIFY_CLIENT_SECRET = $spotifyClientSecret
                
                $command3 = "python scripts/generate_spotify_playlists.py --festival $festivalSlug --year $year"
                Write-Host "Running: $command3" -ForegroundColor Gray
                Write-Host ""
                
                # Execute interactively (allows user input for missing Spotify links)
                & python scripts/generate_spotify_playlists.py --festival $festivalSlug --year $year
                
                # Check if command succeeded
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Host "✓ Updated Spotify playlist" -ForegroundColor Green
                    Write-Host "✓ Successfully processed all content for $festivalName $year" -ForegroundColor Green
                    $successCount++
                } else {
                    Write-Host ""
                    Write-Host "⚠ Failed to update Spotify playlist for $festivalName $year" -ForegroundColor Yellow
                    Write-Host "⚠ Continuing with other festivals..." -ForegroundColor Yellow
                    $failureCount++
                }
            } else {
                Write-Host "⊘ Skipping Spotify playlist (no credentials)" -ForegroundColor DarkGray
                # Still count as successful since it's optional
                $successCount++
            }
        } else {
            Write-Host "⊘ Skipping Spotify playlist (--SkipPlaylists flag)" -ForegroundColor DarkGray
            Write-Host "✓ Successfully processed all content for $festivalName $year" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "✗ Exception while processing $festivalName $year" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $failureCount++
    }
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
}

# Regenerate homepage (index.html)
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating homepage ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

Write-Host ""
Write-Host "Regenerating homepage..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python scripts/generate_archive_index.py docs"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python scripts/generate_archive_index.py docs 2>&1
    
    # Check if command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Successfully regenerated homepage" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "✗ Failed to regenerate homepage" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        $failureCount++
    }
}
catch {
    Write-Host "✗ Exception while regenerating homepage" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Generate charts page
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating charts page ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

Write-Host ""
Write-Host "Generating charts comparison page..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python scripts/helpers/generate_charts.py"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python scripts/helpers/generate_charts.py 2>&1
    
    # Check if command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Charts page generated successfully" -ForegroundColor Green
        Write-Host $output
        $successCount++
    } else {
        Write-Host "✗ Failed to generate charts page" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        $failureCount++
    }
}
catch {
    Write-Host "✗ Exception while generating charts page" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Generate FAQ page
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating Festival Pages" -Status "Generating FAQ page ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

Write-Host ""
Write-Host "Generating FAQ page..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python scripts/helpers/generate_faq.py"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python scripts/helpers/generate_faq.py 2>&1
    
    # Check if command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FAQ page generated successfully" -ForegroundColor Green
        Write-Host $output
        $successCount++
    } else {
        Write-Host "✗ Failed to generate FAQ page" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        $failureCount++
    }
}
catch {
    Write-Host "✗ Exception while generating FAQ page" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

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

$operationsLabel = if ($SkipPlaylists) { "lineup + about + artist pages each" } else { "lineup + about + artist pages + playlist each" }
Write-Host "Festivals processed: $totalFestivals ($operationsLabel)" -ForegroundColor White
Write-Host "Additional pages: Homepage, Charts, FAQ" -ForegroundColor White
Write-Host "Total operations: $(($totalFestivals * $operationsPerFestival) + 3)" -ForegroundColor White

Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $durationFormatted" -ForegroundColor Gray
Write-Host ""

# Exit with appropriate code
if ($failureCount -eq 0) {
    Write-Host "✓ All pages regenerated successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some operations failed. Check errors above." -ForegroundColor Red
    exit 1
}
