#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Regression test script for LineupRadar
    
.DESCRIPTION
    Runs all generation scripts for both festivals to ensure no regressions.
    Tests the complete pipeline from data fetching to HTML generation.
    
.EXAMPLE
    .\test_regression.ps1
    
.EXAMPLE
    .\test_regression.ps1 -SkipFetch
#>

param(
    [switch]$SkipFetch,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Activate virtual environment if it exists
$venvPath = ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "Warning: Virtual environment not found at $venvPath" -ForegroundColor Yellow
}

$festivals = @("down-the-rabbit-hole", "pinkpop")
$year = 2026
$failedTests = @()
$passedTests = @()

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n=======================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "=======================================`n" -ForegroundColor Cyan
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Details = ""
    )
    
    if ($Success) {
        Write-Host "✓ $TestName" -ForegroundColor Green
        if ($Details -and $Verbose) {
            Write-Host "  $Details" -ForegroundColor Gray
        }
        $script:passedTests += $TestName
    } else {
        Write-Host "✗ $TestName" -ForegroundColor Red
        if ($Details) {
            Write-Host "  Error: $Details" -ForegroundColor Red
        }
        $script:failedTests += $TestName
    }
}

function Test-FileExists {
    param(
        [string]$Path,
        [string]$Description
    )
    
    if (Test-Path $Path) {
        Write-TestResult -TestName $Description -Success $true -Details "File exists: $Path"
        return $true
    } else {
        Write-TestResult -TestName $Description -Success $false -Details "File not found: $Path"
        return $false
    }
}

function Test-CSVRowCount {
    param(
        [string]$Path,
        [int]$ExpectedCount,
        [string]$Description
    )
    
    try {
        # Use Python CSV parser to properly count rows (handles multi-line fields)
        $pythonScript = @"
import csv
import sys
with open(r'$Path', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(len(rows))
"@
        
        $pythonExe = ".venv\Scripts\python.exe"
        $actualCount = & $pythonExe -c $pythonScript
        $actualCount = [int]$actualCount
        
        if ($actualCount -eq $ExpectedCount) {
            Write-TestResult -TestName $Description -Success $true -Details "$actualCount rows"
            return $true
        } else {
            Write-TestResult -TestName $Description -Success $false -Details "Expected $ExpectedCount rows, got $actualCount"
            return $false
        }
    } catch {
        Write-TestResult -TestName $Description -Success $false -Details $_.Exception.Message
        return $false
    }
}

# Start regression tests
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           LineupRadar Regression Test Suite                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

Write-Host "Testing configuration:" -ForegroundColor Yellow
Write-Host "  Festivals: $($festivals -join ', ')" -ForegroundColor Gray
Write-Host "  Year: $year" -ForegroundColor Gray
Write-Host "  Skip fetch: $SkipFetch" -ForegroundColor Gray
Write-Host ""

# Test 1: Check CSV files exist
Write-TestHeader "TEST 1: Verify CSV Files"

foreach ($festival in $festivals) {
    $csvPath = "$festival/$year.csv"
    Test-FileExists -Path $csvPath -Description "CSV exists for $festival $year"
}

# Test 2: Verify CSV data integrity
Write-TestHeader "TEST 2: Verify CSV Data Integrity"

Test-CSVRowCount -Path "down-the-rabbit-hole/$year.csv" -ExpectedCount 39 -Description "Down The Rabbit Hole has 39 artists"
Test-CSVRowCount -Path "pinkpop/$year.csv" -ExpectedCount 32 -Description "Pinkpop has 32 artists"

# Test 3: Run fetch_festival_data.py (optional)
if (-not $SkipFetch) {
    Write-TestHeader "TEST 3: Fetch Festival Data"
    
    foreach ($festival in $festivals) {
        try {
            Write-Host "Fetching data for $festival..." -ForegroundColor Yellow
            python fetch_festival_data.py --festival $festival --year $year 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-TestResult -TestName "fetch_festival_data.py --festival $festival" -Success $true
            } else {
                Write-TestResult -TestName "fetch_festival_data.py --festival $festival" -Success $false -Details "Exit code: $LASTEXITCODE"
            }
        } catch {
            Write-TestResult -TestName "fetch_festival_data.py --festival $festival" -Success $false -Details $_.Exception.Message
        }
    }
} else {
    Write-Host "`nSkipping fetch tests (--SkipFetch flag set)`n" -ForegroundColor Yellow
}

# Test 4: Generate HTML lineup pages
Write-TestHeader "TEST 4: Generate HTML Lineup Pages"

foreach ($festival in $festivals) {
    try {
        Write-Host "Generating HTML for $festival..." -ForegroundColor Yellow
        $env:PYTHONIOENCODING = "utf-8"
        python generate_html.py --festival $festival --year $year 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $outputPath = "docs/$festival/$year/index.html"
            if (Test-Path $outputPath) {
                Write-TestResult -TestName "generate_html.py --festival $festival" -Success $true -Details "Generated: $outputPath"
            } else {
                Write-TestResult -TestName "generate_html.py --festival $festival" -Success $false -Details "Output file not found: $outputPath"
            }
        } else {
            Write-TestResult -TestName "generate_html.py --festival $festival" -Success $false -Details "Exit code: $LASTEXITCODE"
        }
    } catch {
        Write-TestResult -TestName "generate_html.py --festival $festival" -Success $false -Details $_.Exception.Message
    }
}

# Test 5: Generate artist pages
Write-TestHeader "TEST 5: Generate Artist Pages"

foreach ($festival in $festivals) {
    try {
        Write-Host "Generating artist pages for $festival..." -ForegroundColor Yellow
        $env:PYTHONIOENCODING = "utf-8"
        python generate_artist_pages.py --festival $festival --year $year 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $artistDir = "docs/$festival/$year/artists"
            if (Test-Path $artistDir) {
                $artistCount = (Get-ChildItem $artistDir -Filter "*.html").Count
                $expectedCount = if ($festival -eq "down-the-rabbit-hole") { 39 } else { 32 }
                
                if ($artistCount -eq $expectedCount) {
                    Write-TestResult -TestName "generate_artist_pages.py --festival $festival" -Success $true -Details "$artistCount pages"
                } else {
                    Write-TestResult -TestName "generate_artist_pages.py --festival $festival" -Success $false -Details "Expected $expectedCount pages, got $artistCount"
                }
            } else {
                Write-TestResult -TestName "generate_artist_pages.py --festival $festival" -Success $false -Details "Output directory not found: $artistDir"
            }
        } else {
            Write-TestResult -TestName "generate_artist_pages.py --festival $festival" -Success $false -Details "Exit code: $LASTEXITCODE"
        }
    } catch {
        Write-TestResult -TestName "generate_artist_pages.py --festival $festival" -Success $false -Details $_.Exception.Message
    }
}

# Test 6: Generate archive index
Write-TestHeader "TEST 6: Generate Archive Index"

try {
    Write-Host "Generating archive index..." -ForegroundColor Yellow
    $env:PYTHONIOENCODING = "utf-8"
    python generate_archive_index.py 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $indexPath = "docs/index.html"
        if (Test-Path $indexPath) {
            $content = Get-Content $indexPath -Raw
            $hasDTRH = $content -match "Down The Rabbit Hole"
            $hasPinkpop = $content -match "Pinkpop"
            
            if ($hasDTRH -and $hasPinkpop) {
                Write-TestResult -TestName "generate_archive_index.py" -Success $true -Details "Both festivals present"
            } else {
                $missing = @()
                if (-not $hasDTRH) { $missing += "Down The Rabbit Hole" }
                if (-not $hasPinkpop) { $missing += "Pinkpop" }
                Write-TestResult -TestName "generate_archive_index.py" -Success $false -Details "Missing festivals: $($missing -join ', ')"
            }
        } else {
            Write-TestResult -TestName "generate_archive_index.py" -Success $false -Details "Output file not found: $indexPath"
        }
    } else {
        Write-TestResult -TestName "generate_archive_index.py" -Success $false -Details "Exit code: $LASTEXITCODE"
    }
} catch {
    Write-TestResult -TestName "generate_archive_index.py" -Success $false -Details $_.Exception.Message
}

# Test 7: Verify HTML structure
Write-TestHeader "TEST 7: Verify HTML Structure"

foreach ($festival in $festivals) {
    $festivalName = if ($festival -eq "down-the-rabbit-hole") { "Down The Rabbit Hole" } else { "Pinkpop" }
    $indexPath = "docs/$festival/$year/index.html"
    
    if (Test-Path $indexPath) {
        $content = Get-Content $indexPath -Raw
        
        # Check for festival name in content
        if ($content -match [regex]::Escape($festivalName)) {
            Write-TestResult -TestName "$festival index contains festival name" -Success $true
        } else {
            Write-TestResult -TestName "$festival index contains festival name" -Success $false -Details "Festival name not found in HTML"
        }
        
        # Check for year
        if ($content -match $year) {
            Write-TestResult -TestName "$festival index contains year" -Success $true
        } else {
            Write-TestResult -TestName "$festival index contains year" -Success $false -Details "Year not found in HTML"
        }
    }
}

# Test 8: Verify artist page format
Write-TestHeader "TEST 8: Verify Artist Page Format"

foreach ($festival in $festivals) {
    $festivalName = if ($festival -eq "down-the-rabbit-hole") { "Down The Rabbit Hole" } else { "Pinkpop" }
    $artistDir = "docs/$festival/$year/artists"
    
    if (Test-Path $artistDir) {
        $samplePage = Get-ChildItem $artistDir -Filter "*.html" | Select-Object -First 1
        
        if ($samplePage) {
            $content = Get-Content $samplePage.FullName -Raw
            
            # Check for "@ Festival Year" format
            $expectedPattern = "@ $festivalName $year"
            if ($content -match [regex]::Escape($expectedPattern)) {
                Write-TestResult -TestName "$festival artist pages have correct header format" -Success $true -Details "Found: $expectedPattern"
            } else {
                Write-TestResult -TestName "$festival artist pages have correct header format" -Success $false -Details "Expected pattern not found: $expectedPattern"
            }
        }
    }
}

# Final summary
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                      TEST SUMMARY                            ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

Write-Host "Passed: $($passedTests.Count)" -ForegroundColor Green
Write-Host "Failed: $($failedTests.Count)" -ForegroundColor $(if ($failedTests.Count -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failedTests.Count -gt 0) {
    Write-Host "Failed tests:" -ForegroundColor Red
    foreach ($test in $failedTests) {
        Write-Host "  - $test" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
} else {
    Write-Host "🎉 All tests passed! No regressions detected." -ForegroundColor Green
    Write-Host ""
    exit 0
}
