#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regenerate all HTML pages for all festivals and years
.DESCRIPTION
    This script regenerates both lineup index pages and individual artist pages 
    for all configured festivals and years. It runs generate_html.py followed by 
    generate_artist_pages.py for each festival/year combination.
.EXAMPLE
    .\regenerate_all.ps1
#>

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
$festivals = @(
    @{
        Name = "Down The Rabbit Hole"
        Slug = "down-the-rabbit-hole"
        Year = 2026
    },
    @{
        Name = "Pinkpop"
        Slug = "pinkpop"
        Year = 2026
    },
    @{
        Name = "Rock Werchter"
        Slug = "rock-werchter"
        Year = 2026
    }
)

# Track success/failure
$totalFestivals = $festivals.Count
$successCount = 0
$failureCount = 0
$startTime = Get-Date

# Process each festival
foreach ($festival in $festivals) {
    $festivalName = $festival.Name
    $festivalSlug = $festival.Slug
    $year = $festival.Year
    
    Write-Host "Processing: $festivalName $year..." -ForegroundColor Yellow
    Write-Host "Festival slug: $festivalSlug" -ForegroundColor Gray
    Write-Host ""
    
    try {
        # Run the lineup index page generation script
        $command1 = "python generate_html.py --festival $festivalSlug --year $year"
        Write-Host "Running: $command1" -ForegroundColor Gray
        
        # Execute and capture output
        $output1 = & python generate_html.py --festival $festivalSlug --year $year 2>&1
        
        # Check if command succeeded
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Failed to generate lineup index for $festivalName $year" -ForegroundColor Red
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $output1 -ForegroundColor Red
            $failureCount++
            continue
        }
        
        Write-Host "✓ Generated lineup index page" -ForegroundColor Green
        
        # Run the artist pages generation script
        $command2 = "python generate_artist_pages.py --festival $festivalSlug --year $year"
        Write-Host "Running: $command2" -ForegroundColor Gray
        
        # Execute and capture output
        $output2 = & python generate_artist_pages.py --festival $festivalSlug --year $year 2>&1
        
        # Check if command succeeded
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Generated artist pages" -ForegroundColor Green
            Write-Host "✓ Successfully generated all pages for $festivalName $year" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Failed to generate artist pages for $festivalName $year" -ForegroundColor Red
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $output2 -ForegroundColor Red
            $failureCount++
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
Write-Host ""
Write-Host "Regenerating homepage..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python generate_archive_index.py docs"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python generate_archive_index.py docs 2>&1
    
    # Check if command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Successfully regenerated homepage" -ForegroundColor Green
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
Write-Host ""
Write-Host "Generating charts comparison page..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python generate_charts.py"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python generate_charts.py 2>&1
    
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

# Update FAQ timestamps
Write-Host ""
Write-Host "Updating FAQ timestamps..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python update_faq_timestamps.py"
    Write-Host "Running: $command" -ForegroundColor Gray
    
    # Execute and capture output
    $output = & python update_faq_timestamps.py 2>&1
    
    # Check if command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Successfully updated FAQ timestamps" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to update FAQ timestamps" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        $failureCount++
    }
}
catch {
    Write-Host "✗ Exception while updating FAQ timestamps" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

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
Write-Host "Total festivals processed: $totalFestivals" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $durationSeconds seconds" -ForegroundColor Gray
Write-Host ""

# Exit with appropriate code
if ($failureCount -eq 0) {
    Write-Host "✓ All HTML pages regenerated successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some festivals failed to regenerate. Check errors above." -ForegroundColor Red
    exit 1
}
