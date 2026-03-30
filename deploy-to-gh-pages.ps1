# deploy-to-gh-pages.ps1
# Run this script to automatically deploy to GitHub Pages

Write-Host "Deploying USTED frontend to GitHub Pages..." -ForegroundColor Cyan

cd "C:\Users\AKMC\Desktop\Research Project V.1"

# Save current branch
$currentBranch = git branch --show-current

# Create or switch to gh-pages branch
git checkout gh-pages 2>$null
if ($LASTEXITCODE -ne 0) {
    git checkout -b gh-pages
    Write-Host "✅ Created gh-pages branch" -ForegroundColor Green
}

# Remove all files except .git
git rm -rf . 2>$null
Write-Host "✅ Cleaned gh-pages branch" -ForegroundColor Green

# Copy files from deployment folder
Copy-Item -Path "gh_pages_deploy\*" -Destination . -Recurse -Force
Write-Host "✅ Copied deployment files" -ForegroundColor Green

# Add all files
git add .
Write-Host "✅ Staged files" -ForegroundColor Green

# Commit
git commit -m "Deploy USTED frontend to GitHub Pages"
Write-Host "✅ Committed changes" -ForegroundColor Green

# Push to gh-pages
git push origin gh-pages --force
Write-Host "✅ Pushed to gh-pages branch" -ForegroundColor Green

# Switch back to original branch
git checkout $currentBranch
Write-Host "✅ Switched back to $currentBranch branch" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your site will be available at:" -ForegroundColor Cyan
Write-Host "   https://kumah-caleb.github.io/Research-Project-V.1/" -ForegroundColor White
Write-Host ""
Write-Host "⏱️  It may take 2-5 minutes for GitHub Pages to update." -ForegroundColor Yellow
Write-Host ""
