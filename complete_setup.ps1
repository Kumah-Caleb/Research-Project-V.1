Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "STUDENT PERFORMANCE PREDICTION SYSTEM - COMPLETE SETUP" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Check Node.js
Write-Host "`n[1/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node.js not found"
    }
} catch {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check Python
Write-Host "`n[2/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from: https://python.org/" -ForegroundColor Yellow
    exit 1
}

# Create requirements.txt if it doesn't exist
Write-Host "`n[3/6] Creating requirements.txt..." -ForegroundColor Yellow
if (-not (Test-Path "requirements.txt")) {
    @"
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
"@ | Out-File -FilePath requirements.txt -Encoding utf8
    Write-Host "✅ Created requirements.txt" -ForegroundColor Green
} else {
    Write-Host "✅ requirements.txt already exists" -ForegroundColor Green
}

# Install Python dependencies
Write-Host "`n[4/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some packages may have issues, but continuing..." -ForegroundColor Yellow
}

# Create package.json if it doesn't exist
Write-Host "`n[5/6] Creating package.json..." -ForegroundColor Yellow
if (-not (Test-Path "package.json")) {
    @"
{
  "name": "student-performance-predictor",
  "version": "1.0.0",
  "description": "Student Performance Prediction System",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
"@ | Out-File -FilePath package.json -Encoding utf8
    Write-Host "✅ Created package.json" -ForegroundColor Green
} else {
    Write-Host "✅ package.json already exists" -ForegroundColor Green
}

# Install Node.js dependencies
Write-Host "`n[6/6] Installing Node.js dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Node.js dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some packages may have issues, but continuing..." -ForegroundColor Yellow
}

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✨ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Train the model: python train_model.py" -ForegroundColor Cyan
Write-Host "2. Start the server: node server.js" -ForegroundColor Cyan
Write-Host "3. Open browser: http://localhost:3000" -ForegroundColor Cyan
