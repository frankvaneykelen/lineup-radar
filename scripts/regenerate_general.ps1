#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regenerate general/non-festival HTML pages
.DESCRIPTION
    This script regenerates the homepage (index.html), charts page, and FAQ page.
    It does not regenerate any festival-specific pages.
    
.EXAMPLE
    .\regenerate_general.ps1
    Regenerates homepage, charts, and FAQ pages.
#>

# Set error action preference
$ErrorActionPreference = "Stop"

# Set console output encoding to UTF-8 to handle Unicode characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regenerating General Pages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Track success/failure
$totalOperations = 3  # homepage + charts + FAQ
$currentOperation = 0
$successCount = 0
$failureCount = 0
$startTime = Get-Date

# 1. Regenerate homepage (index.html)
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating General Pages" -Status "Generating homepage ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

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

# 2. Generate charts page
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating General Pages" -Status "Generating charts page ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

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

# 3. Generate FAQ page
$currentOperation++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating General Pages" -Status "Generating FAQ page ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

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
Write-Progress -Activity "Regenerating General Pages" -Status "Complete" -Completed


# 4. Regenerate all festival README files
$currentOperation++
$totalOperations++
$percentComplete = [int](($currentOperation / $totalOperations) * 100)
Write-Progress -Activity "Regenerating General Pages" -Status "Generating festival READMEs ($currentOperation of $totalOperations)" -PercentComplete $percentComplete

Write-Host "Regenerating all festival README files..." -ForegroundColor Yellow
Write-Host ""

try {
    $command = "python scripts/generate_festival_readme.py --all"
    Write-Host "Running: $command" -ForegroundColor Gray
    $output = & python scripts/generate_festival_readme.py --all 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Festival READMEs generated successfully" -ForegroundColor Green
        Write-Host $output
        $successCount++
    } else {
        Write-Host "✗ Failed to generate festival READMEs" -ForegroundColor Red
        Write-Host "Error output:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        $failureCount++
    }
}
catch {
    Write-Host "✗ Exception while generating festival READMEs" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $failureCount++
}

# Calculate duration
$endTime = Get-Date
$duration = $endTime - $startTime
$durationFormatted = "{0:00}:{1:00}:{2:00}" -f [int]$duration.TotalHours, $duration.Minutes, $duration.Seconds

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Regeneration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Pages regenerated: Homepage, Charts, FAQ, Festival READMEs" -ForegroundColor White
Write-Host "Total operations: $totalOperations" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $durationFormatted" -ForegroundColor Gray
Write-Host ""

# Exit with appropriate code
if ($failureCount -eq 0) {
    Write-Host "✓ All general pages regenerated successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some operations failed. Check errors above." -ForegroundColor Red
    exit 1
}
