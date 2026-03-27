# Server Management Script for Student Performance Predictor

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "start"
)

$serverDir = "C:\Users\AKMC\Desktop\Research Project V.1\backend"
$port = 3000

function Stop-Server {
    Write-Host "🔍 Checking for running server on port $port..." -ForegroundColor Yellow
    
    # Find process using the port
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    
    if ($process) {
        $pid = $process.OwningProcess
        Write-Host "   Found process with PID: $pid" -ForegroundColor Yellow
        
        # Stop the process
        Stop-Process -Id $pid -Force
        Write-Host "✅ Server stopped successfully" -ForegroundColor Green
        return $true
    } else {
        Write-Host "ℹ️ No server running on port $port" -ForegroundColor Cyan
        return $false
    }
}

function Start-Server {
    Write-Host "🚀 Starting server..." -ForegroundColor Yellow
    
    # Check if port is already in use
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "⚠️ Port $port is already in use!" -ForegroundColor Red
        $response = Read-Host "Do you want to stop the existing server and start a new one? (Y/N)"
        
        if ($response -eq 'Y' -or $response -eq 'y') {
            Stop-Server
            Start-Sleep -Seconds 2
        } else {
            Write-Host "❌ Cannot start server. Port $port is occupied." -ForegroundColor Red
            return
        }
    }
    
    # Change to backend directory
    Push-Location $serverDir
    
    # Start the server
    $process = Start-Process node -ArgumentList "server.js" -PassThru -NoNewWindow
    
    Pop-Location
    
    Write-Host "✅ Server started with PID: $($process.Id)" -ForegroundColor Green
    Write-Host "🌐 Server running at: http://localhost:$port" -ForegroundColor Cyan
    Write-Host "📝 Press Ctrl+C to stop the server" -ForegroundColor Yellow
}

function Get-Status {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    
    if ($process) {
        $pid = $process.OwningProcess
        Write-Host "✅ Server is running on port $port (PID: $pid)" -ForegroundColor Green
        
        # Try to get more details about the process
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "   Process Name: $($proc.ProcessName)" -ForegroundColor Gray
            Write-Host "   Memory Usage: $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
            Write-Host "   CPU Time: $($proc.CPU)" -ForegroundColor Gray
            Write-Host "   Start Time: $($proc.StartTime)" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ No server is running on port $port" -ForegroundColor Red
    }
}

# Main action handler
switch ($Action) {
    "start" { Start-Server }
    "stop" { Stop-Server }
    "restart" {
        Stop-Server
        Start-Sleep -Seconds 2
        Start-Server
    }
    "status" { Get-Status }
    default {
        Write-Host "Invalid action. Use: start, stop, restart, or status" -ForegroundColor Red
    }
}
