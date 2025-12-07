#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regenerate all HTML pages for all festivals and years
.DESCRIPTION
    This script regenerates both lineup index pages and individual artist pages 
    for all configured festivals and years. It runs generate_html.py followed by 
    generate_artist_pages.py for each festival/year combination.
    
.PARAMETER Festival
    Optional festival slug. If specified, only regenerates pages for that festival.
    Valid values: best-kept-secret, down-the-rabbit-hole, pinkpop, rock-werchter, footprints

.PARAMETER GeneralPagesOnly
    If specified, only regenerates general pages (homepage, charts, FAQ) and skips all festival-specific pages.

.EXAMPLE
    .\regenerate_all.ps1
    Regenerates all pages for all festivals.

.EXAMPLE
    .\regenerate_all.ps1 -Festival best-kept-secret
    Regenerates pages only for Best Kept Secret 2026.

.EXAMPLE
    .\regenerate_all.ps1 -GeneralPagesOnly
    Regenerates only homepage, charts, and FAQ pages.
#>

param(
    [string]$Festival,
    [switch]$GeneralPagesOnly
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

# Validate festival parameter if provided
$singleFestival = $null
if ($Festival) {
    $validSlugs = $allFestivals | ForEach-Object { $_.Slug }
    if ($Festival -notin $validSlugs) {
        Write-Host "✗ Invalid festival slug: $Festival" -ForegroundColor Red
        Write-Host "Valid values: $($validSlugs -join ', ')" -ForegroundColor Yellow
        exit 1
    }
    
    # Filter to only the requested festival
    foreach ($f in $allFestivals) {
        if ($f.Slug -eq $Festival) {
            $singleFestival = $f
            break
        }
    }
    Write-Host "Filtering to festival: $($singleFestival.Name)" -ForegroundColor Cyan
    Write-Host ""
} elseif ($GeneralPagesOnly) {
    # No festival processing needed  
    Write-Host "Skipping festival-specific pages (--GeneralPagesOnly mode)" -ForegroundColor Cyan
    Write-Host ""
} else {
    # Process all festivals - use the original array
    $festivalsToProcess = $allFestivals
}


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
# Determine which festivals to process
if ($singleFestival) {
    $festivalsToProcess = @($singleFestival)
    $totalFestivals = 1
} elseif ($GeneralPagesOnly) {
    $festivalsToProcess = @()
    $totalFestivals = 0
} else {
    # $festivalsToProcess already set to $allFestivals above
    $totalFestivals = $festivalsToProcess.Count
}

$totalOperations = ($totalFestivals * 4) + 3  # Each festival: lineup + artist pages + about page + playlist, plus homepage + charts + FAQ
$currentOperation = 0
$successCount = 0
$failureCount = 0
$startTime = Get-Date

# Process each festival
$festivalIndex = 0
foreach ($fest in $festivalsToProcess) {
    # Workaround: Re-fetch from original source to avoid PowerShell type conversion bug
    if ($singleFestival) {
        $festival = $singleFestival
    } else {
        $festival = $allFestivals[$festivalIndex]
    }
    
    $festivalName = $festival.Name
    $festivalSlug = $festival.Slug
    $year = $festival.Year
    
    $currentOperation++
    $percentComplete = [int](($currentOperation / $totalOperations) * 100)
    Write-Progress -Activity "Regenerating Festival Pages" -Status "Processing $festivalName $year ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
    
    $festivalIndex++
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
        
        # Update progress for Spotify playlist
        $currentOperation++
        $percentComplete = [int](($currentOperation / $totalOperations) * 100)
        Write-Progress -Activity "Regenerating Festival Pages" -Status "Updating Spotify playlist for $festivalName ($currentOperation of $totalOperations)" -PercentComplete $percentComplete
        
        # Generate/update Spotify playlist if credentials are available
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
$durationSeconds = [math]::Round($duration.TotalSeconds, 2)

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regeneration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($GeneralPagesOnly) {
    Write-Host "Mode: General pages only" -ForegroundColor White
    Write-Host "Pages regenerated: Homepage, Charts, FAQ" -ForegroundColor White
    Write-Host "Total operations: 3" -ForegroundColor White
} elseif ($Festival) {
    Write-Host "Mode: Single festival ($($allFestivals | Where-Object { $_.Slug -eq $Festival } | ForEach-Object { $_.Name }))" -ForegroundColor White
    Write-Host "Festival operations: 1 festival × 4 operations (lineup + about + artist pages + playlist)" -ForegroundColor White
    Write-Host "Additional pages: Homepage, Charts, FAQ" -ForegroundColor White
    Write-Host "Total operations: 7" -ForegroundColor White
} else {
    Write-Host "Mode: All festivals" -ForegroundColor White
    Write-Host "Festivals processed: $totalFestivals (lineup + about + artist pages + playlist each)" -ForegroundColor White
    Write-Host "Additional pages: Homepage, Charts, FAQ" -ForegroundColor White
    Write-Host "Total operations: $(($totalFestivals * 4) + 3)" -ForegroundColor White
}

Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $durationSeconds seconds" -ForegroundColor Gray
Write-Host ""

# Exit with appropriate code
if ($failureCount -eq 0) {
    Write-Host "✓ All pages regenerated successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some operations failed. Check errors above." -ForegroundColor Red
    exit 1
}
