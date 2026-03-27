# fix-encoding.ps1
# Run this script to fix all character encoding issues in your project

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "FIXING CHARACTER ENCODING ISSUES" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# Set the project path
$projectPath = "C:\Users\AKMC\Desktop\Research Project V.1"
Set-Location $projectPath

# Create a backup folder
$backupFolder = "C:\Users\AKMC\Desktop\encoding_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
Write-Host "`n📁 Backup folder created: $backupFolder" -ForegroundColor Yellow

# Define broken emoji patterns and their replacements
$emojiMap = @{
    # Broken patterns
    'ðŸ‘©â€ðŸ«' = '👩‍🏫'
    'ðŸ‘¨â€ðŸŽ“' = '👨‍🎓'
    'ðŸ‘©â€ðŸŽ“' = '👩‍🎓'
    'ðŸ‘¨â€ðŸ«' = '👨‍🏫'
    'ðŸ“š' = '📚'
    'ðŸ“…' = '📅'
    'âœï¸' = '✏️'
    'âœ…' = '✅'
    'âŒ' = '❌'
    'ðŸš€' = '🚀'
    'ðŸ”' = '🔐'
    'ðŸ“' = '📝'
    'ðŸ“Š' = '📊'
    'ðŸ‘¤' = '👤'
    'ðŸ“˜' = '📘'
    'ðŸŽ“' = '🎓'
    'ðŸ’¡' = '💡'
    'ðŸ“ˆ' = '📈'
    'ðŸ’¾' = '💾'
    'ðŸ”®' = '🔮'
    'âš™ï¸' = '⚠️'
    'ðŸ˜Š' = '😊'
    'ðŸ‘‹' = '👋'
    'ðŸŽ‰' = '🎉'
    'ðŸ“‚' = '📂'
    'ðŸ“' = '📍'
    'ðŸ“©' = '📩'
    'ðŸ“§' = '📧'
    'ðŸ“ž' = '📞'
    'ðŸ“±' = '📱'
    'ðŸ’»' = '💻'
    'ðŸ–¥' = '🖥️'
    'ðŸ–±' = '🖱️'
    'ðŸ“Ÿ' = '📟'
    'ðŸ“ ' = '📠'
    'ðŸ“¤' = '📤'
    'ðŸ“¥' = '📥'
    'ðŸ“¦' = '📦'
    'ðŸ“«' = '📫'
    'ðŸ“¬' = '📬'
    'ðŸ“­' = '📭'
    'ðŸ“®' = '📮'
    'ðŸ“¯' = '📯'
    'ðŸ“°' = '📰'
    'ðŸ“±' = '📱'
    'ðŸ“²' = '📲'
    'ðŸ“³' = '📳'
    'ðŸ“´' = '📴'
}

# Function to fix a single file
function Fix-FileEncoding {
    param(
        [string]$FilePath,
        [hashtable]$Replacements
    )
    
    try {
        # Read file with UTF-8 encoding
        $content = Get-Content $FilePath -Raw -Encoding UTF8 -ErrorAction Stop
        
        # Check if file contains any broken patterns
        $hasIssues = $false
        foreach ($pattern in $Replacements.Keys) {
            if ($content -match $pattern) {
                $hasIssues = $true
                break
            }
        }
        
        if (-not $hasIssues) {
            return $false
        }
        
        # Create backup
        $relativePath = $FilePath.Replace($projectPath, "").TrimStart('\')
        $backupPath = Join-Path $backupFolder $relativePath
        $backupDir = Split-Path $backupPath -Parent
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        Copy-Item $FilePath $backupPath -Force
        
        # Replace broken patterns
        foreach ($pattern in $Replacements.Keys) {
            $content = $content -replace $pattern, $Replacements[$pattern]
        }
        
        # Save with UTF-8 encoding
        $content | Out-File -FilePath $FilePath -Encoding UTF8 -NoNewline
        
        return $true
    }
    catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
        return $false
    }
}

# Collect all files to process
Write-Host "`n📂 Scanning for files with encoding issues..." -ForegroundColor Yellow

$htmlFiles = Get-ChildItem -Path $projectPath -Recurse -Include "*.html", "*.py", "*.js", "*.css" | Where-Object {
    $_.FullName -notmatch "node_modules|\.git|backup"
}

$fixedCount = 0
$processedFiles = @()

foreach ($file in $htmlFiles) {
    $fixed = Fix-FileEncoding -FilePath $file.FullName -Replacements $emojiMap
    if ($fixed) {
        $fixedCount++
        $processedFiles += $file.FullName
        Write-Host "  ✅ Fixed: $($file.Name)" -ForegroundColor Green
    }
}

# Add meta charset to HTML files if missing
Write-Host "`n📄 Adding meta charset to HTML files..." -ForegroundColor Yellow

$htmlFiles = Get-ChildItem -Path "docs" -Recurse -Include "*.html" | Where-Object {
    $_.FullName -notmatch "\.git|backup"
}

$charsetAdded = 0
foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    if ($content -notmatch '<meta charset="UTF-8">') {
        # Add meta charset right after <head>
        $content = $content -replace '(<head[^>]*>)', '$1`n    <meta charset="UTF-8">'
        $content | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline
        $charsetAdded++
        Write-Host "  ✅ Added charset to: $($file.Name)" -ForegroundColor Green
    }
}

# Create a proper emoji replacement function for Python files
Write-Host "`n🐍 Updating Python files..." -ForegroundColor Yellow

$pythonFiles = Get-ChildItem -Path $projectPath -Filter "*.py" | Where-Object {
    $_.FullName -notmatch "\.git|backup"
}

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    if ($content -match 'ðŸ|âœ|â') {
        foreach ($pattern in $emojiMap.Keys) {
            $content = $content -replace $pattern, $emojiMap[$pattern]
        }
        $content | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline
        Write-Host "  ✅ Fixed Python: $($file.Name)" -ForegroundColor Green
        $fixedCount++
    }
}

# Create a CSS class for emoji fallback (optional)
Write-Host "`n🎨 Creating emoji fallback CSS..." -ForegroundColor Yellow

$emojiCss = @"
/* Emoji fallback for older browsers */
.emoji {
    font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif;
}

/* Custom icons as fallback */
.icon-lecturer::before { content: "👩‍🏫 "; }
.icon-student::before { content: "👨‍🎓 "; }
.icon-book::before { content: "📚 "; }
.icon-calendar::before { content: "📅 "; }
.icon-edit::before { content: "✏️ "; }
.icon-success::before { content: "✅ "; }
.icon-error::before { content: "❌ "; }
.icon-rocket::before { content: "🚀 "; }
"@

$emojiCss | Out-File -FilePath "docs/css/emoji-fallback.css" -Encoding UTF8 -Force
Write-Host "  ✅ Created emoji fallback CSS" -ForegroundColor Green

# Add CSS link to HTML files
Write-Host "`n🔗 Adding emoji fallback CSS to HTML files..." -ForegroundColor Yellow

$htmlFiles = Get-ChildItem -Path "docs" -Recurse -Include "*.html" | Where-Object {
    $_.FullName -notmatch "\.git|backup"
}

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    if ($content -notmatch 'emoji-fallback\.css' -and $content -match '<head>') {
        $cssLink = '    <link rel="stylesheet" href="css/emoji-fallback.css">'
        $content = $content -replace '(<head>)', "`$1`n$cssLink"
        $content | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline
        Write-Host "  ✅ Added CSS to: $($file.Name)" -ForegroundColor Green

