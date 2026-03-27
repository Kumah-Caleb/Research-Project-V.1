# safe-fix-encoding.ps1
# This script replaces emojis with text icons - SAFE and won't break your files

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "SAFE ENCODING FIX - Replacing Emojis with Text" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

cd "C:\Users\AKMC\Desktop\Research Project V.1"

# Create backup first
$backupFolder = "C:\Users\AKMC\Desktop\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
Write-Host "✅ Backup created at: $backupFolder" -ForegroundColor Green

# Define replacements - using text instead of emojis
$replacements = @{
    # Common broken emoji patterns
    'ðŸ‘©â€ðŸ«' = '[Lecturer]'
    'ðŸ‘¨â€ðŸŽ“' = '[Student]'
    'ðŸ“š' = '[Books]'
    'ðŸ“…' = '[Calendar]'
    'âœï¸' = '[Edit]'
    'âœ…' = '[OK]'
    'âŒ' = '[X]'
    'ðŸš€' = '[Launch]'
    'ðŸ”' = '[Lock]'
    'ðŸ“' = '[Notes]'
    'ðŸ“Š' = '[Stats]'
    'ðŸ‘¤' = '[Profile]'
    'ðŸŽ“' = '[Graduate]'
    'ðŸ’¡' = '[Idea]'
    'ðŸ“ˆ' = '[Chart]'
    'ðŸ’¾' = '[Save]'
    'ðŸ”®' = '[Predict]'
    'âš™ï¸' = '[Warning]'
    'ðŸ‘‹' = '[Wave]'
    'ðŸŽ‰' = '[Celebrate]'
}

# Function to fix a file safely
function Fix-FileSafely {
    param($FilePath)
    
    try {
        $content = Get-Content $FilePath -Raw -ErrorAction Stop
        
        # Check if file has issues
        $hasIssues = $false
        foreach ($pattern in $replacements.Keys) {
            if ($content -match $pattern) {
                $hasIssues = $true
                break
            }
        }
        
        if (-not $hasIssues) {
            return $false
        }
        
        # Create backup
        $relativePath = $FilePath.Replace("C:\Users\AKMC\Desktop\Research Project V.1", "").TrimStart('\')
        $backupPath = Join-Path $backupFolder $relativePath
        $backupDir = Split-Path $backupPath -Parent
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        Copy-Item $FilePath $backupPath -Force
        
        # Replace patterns
        foreach ($pattern in $replacements.Keys) {
            $content = $content -replace $pattern, $replacements[$pattern]
        }
        
        # Save with UTF-8 without BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($FilePath, $content, $utf8NoBom)
        
        return $true
    }
    catch {
        Write-Host "  Error: $_" -ForegroundColor Red
        return $false
    }
}

# Process HTML files
Write-Host "`n📄 Processing HTML files..." -ForegroundColor Yellow
$htmlFiles = Get-ChildItem -Path "docs" -Filter "*.html" -Recurse
$fixedCount = 0

foreach ($file in $htmlFiles) {
    if (Fix-FileSafely -FilePath $file.FullName) {
        $fixedCount++
        Write-Host "  ✅ Fixed: $($file.Name)" -ForegroundColor Green
    }
}

# Process Python files
Write-Host "`n🐍 Processing Python files..." -ForegroundColor Yellow
$pyFiles = Get-ChildItem -Path "." -Filter "*.py"
foreach ($file in $pyFiles) {
    if (Fix-FileSafely -FilePath $file.FullName) {
        $fixedCount++
        Write-Host "  ✅ Fixed: $($file.Name)" -ForegroundColor Green
    }
}

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✅ FIX COMPLETE!" -ForegroundColor Green
Write-Host "Files fixed: $fixedCount" -ForegroundColor Yellow
Write-Host "Backup at: $backupFolder" -ForegroundColor Yellow
Write-Host "`nNow run: git add . && git commit -m 'Fix encoding issues' && git push origin main" -ForegroundColor Cyan where do i place these codes