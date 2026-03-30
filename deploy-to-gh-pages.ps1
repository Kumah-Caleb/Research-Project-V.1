# deploy-to-gh-pages.ps1
# Run this script to deploy your frontend to GitHub Pages root

Write-Host "Deploying to GitHub Pages..." -ForegroundColor Cyan

# Save current branch
$currentBranch = git branch --show-current

# Create or switch to gh-pages branch
git checkout gh-pages 2>$null
if ($LASTEXITCODE -ne 0) {
    git checkout -b gh-pages
}

# Remove all files except .git
git rm -rf . 2>$null

# Copy files from temp folder
Copy-Item -Path "temp_gh_pages_deploy\*" -Destination . -Recurse -Force

# Add all files
git add .

# Commit
git commit -m "Deploy frontend to GitHub Pages"

# Push to gh-pages branch
git push origin gh-pages --force

# Switch back to original branch
git checkout $currentBranch

Write-Host "✅ Deployed to GitHub Pages!" -ForegroundColor Green
Write-Host "🌐 Your site will be available at: https://kumah-caleb.github.io/Research-Project-V.1/" -ForegroundColor Cyan
