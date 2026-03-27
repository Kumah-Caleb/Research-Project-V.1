# git-encoding-fix.ps1
# Run this script to configure Git to handle encoding properly

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "CONFIGURING GIT FOR PROPER ENCODING" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# Navigate to your project
cd "C:\Users\AKMC\Desktop\Research Project V.1"

Write-Host "`n[1/6] Configuring Git global settings..." -ForegroundColor Yellow

# Configure Git to handle UTF-8 properly
git config --global core.autocrlf false
git config --global core.safecrlf false
git config --global core.quotepath false
git config --global i18n.commitEncoding utf-8
git config --global i18n.logOutputEncoding utf-8
git config --global gui.encoding utf-8

Write-Host "✅ Git global encoding settings configured" -ForegroundColor Green

Write-Host "`n[2/6] Configuring local repository settings..." -ForegroundColor Yellow

# Configure local repo
git config core.autocrlf false
git config core.safecrlf false
git config core.quotepath false

Write-Host "✅ Local repository settings configured" -ForegroundColor Green

Write-Host "`n[3/6] Creating .gitattributes file..." -ForegroundColor Yellow

# Create .gitattributes to handle file types properly
@"
# Auto detect text files and perform LF normalization
* text=auto

# Source code files
*.html text diff=html
*.css text diff=css
*.js text diff=javascript
*.py text diff=python
*.json text
*.md text

# Explicitly declare text files we want to always be normalized and converted
# to native line endings on checkout
*.html text eol=lf
*.css text eol=lf
*.js text eol=lf
*.py text eol=lf
*.json text eol=lf

# Binary files (should not be modified)
*.png binary
*.jpg binary
*.ico binary
*.pkl binary
*.db binary

# Ensure UTF-8 for text files
*.html working-tree-encoding=UTF-8
*.css working-tree-encoding=UTF-8
*.js working-tree-encoding=UTF-8
*.py working-tree-encoding=UTF-8
*.json working-tree-encoding=UTF-8

# Set charset for diff
*.html diff=html
*.css diff=css
*.js diff=javascript
*.py diff=python
"@ | Out-File -FilePath ".gitattributes" -Encoding utf8

Write-Host "✅ .gitattributes file created" -ForegroundColor Green

Write-Host "`n[4/6] Adding .gitattributes to git..." -ForegroundColor Yellow
git add .gitattributes
git commit -m "Add .gitattributes for proper encoding" 2>$null
Write-Host "✅ .gitattributes added to repository" -ForegroundColor Green

Write-Host "`n[5/6] Checking current files for encoding issues..." -ForegroundColor Yellow

# Check which files have non-ASCII characters
$filesWithIssues = @()
Get-ChildItem -Recurse -Include "*.html", "*.py", "*.js", "*.css" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match '[^\x00-\x7F]') {
        $filesWithIssues += $_.FullName
        Write-Host "  Found non-ASCII in: $($_.Name)" -ForegroundColor Yellow
    }
}

if ($filesWithIssues.Count -gt 0) {
    Write-Host "`n⚠️ Found $($filesWithIssues.Count) files with non-ASCII characters" -ForegroundColor Yellow
    Write-Host "These will be handled by Git's encoding settings" -ForegroundColor Cyan
} else {
    Write-Host "✅ No encoding issues detected" -ForegroundColor Green
}

Write-Host "`n[6/6] Adding and committing all files..." -ForegroundColor Yellow

# Add all files
git add .
git commit -m "Update files with proper encoding settings" 2>$null

Write-Host "✅ Files added to git" -ForegroundColor Green

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "✅ CONFIGURATION COMPLETE!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`n📋 Summary:" -ForegroundColor Yellow
Write-Host "   • Git encoding configured for UTF-8" -ForegroundColor Green
Write-Host "   • .gitattributes created for proper file handling" -ForegroundColor Green
Write-Host "   • Files prepared for push" -ForegroundColor Green

Write-Host "`n🚀 Now push to GitHub:" -ForegroundColor Yellow
Write-Host "   git push origin main" -ForegroundColor Cyan

# Ask if user wants to push now
$pushNow = Read-Host "`nDo you want to push to GitHub now? (y/n)"
if ($pushNow -eq 'y') {
    Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
    git push origin main
    Write-Host "✅ Push complete!" -ForegroundColor Green
    Write-Host "📍 Your site: https://kumah-caleb.github.io/Research-Project-V.1/" -ForegroundColor Cyan
} else {
    Write-Host "`nTo push manually, run: git push origin main" -ForegroundColor Cyan
}