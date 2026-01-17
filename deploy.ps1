# PowerShell Script for Windows - Transfer Files to VPS
# Run this in PowerShell

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    
    [Parameter(Mandatory=$false)]
    [string]$VpsUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$LocalDir = "C:\Work\tg bot\BIG MUMABI",
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteDir = "~/telegram-bot"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Telegram Bot File Transfer Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Transferring files from:" -ForegroundColor Yellow
Write-Host "  Local: $LocalDir" -ForegroundColor White
Write-Host "  Remote: ${VpsUser}@${VpsIp}:${RemoteDir}" -ForegroundColor White
Write-Host ""

# Check if PSCP (PuTTY SCP) is available, otherwise use SCP
$usePscp = $false
if (Get-Command pscp -ErrorAction SilentlyContinue) {
    $usePscp = $true
    Write-Host "Using PSCP (PuTTY) for transfer..." -ForegroundColor Green
} elseif (Get-Command scp -ErrorAction SilentlyContinue) {
    Write-Host "Using SCP for transfer..." -ForegroundColor Green
} else {
    Write-Host "Error: Neither 'pscp' nor 'scp' found!" -ForegroundColor Red
    Write-Host "Please install:" -ForegroundColor Yellow
    Write-Host "  - PuTTY (includes pscp.exe)" -ForegroundColor White
    Write-Host "  - Or use Git Bash with scp" -ForegroundColor White
    Write-Host "  - Or use WSL (Windows Subsystem for Linux)" -ForegroundColor White
    exit 1
}

# Transfer files
Write-Host "Transferring files..." -ForegroundColor Yellow

try {
    if ($usePscp) {
        # Using PSCP (PuTTY)
        $files = Get-ChildItem -Path $LocalDir -File | Where-Object { 
            $_.Extension -in @('.py', '.txt', '.md', '.db') -or 
            $_.Name -eq '.env' 
        }
        
        foreach ($file in $files) {
            Write-Host "  Transferring: $($file.Name)" -ForegroundColor Gray
            & pscp -scp "$($file.FullName)" "${VpsUser}@${VpsIp}:${RemoteDir}/"
        }
    } else {
        # Using SCP
        & scp -r "$LocalDir\*" "${VpsUser}@${VpsIp}:${RemoteDir}/"
    }
    
    Write-Host ""
    Write-Host "Files transferred successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps on VPS:" -ForegroundColor Yellow
    Write-Host "1. SSH to your VPS: ssh ${VpsUser}@${VpsIp}" -ForegroundColor White
    Write-Host "2. Edit .env file: nano ${RemoteDir}/.env" -ForegroundColor White
    Write-Host "3. Start the bot: sudo systemctl start telegram-bot.service" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "Error during transfer: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative methods:" -ForegroundColor Yellow
    Write-Host "1. Use FileZilla (SFTP)" -ForegroundColor White
    Write-Host "2. Use WinSCP" -ForegroundColor White
    Write-Host "3. Use Git Bash: bash transfer-files.sh" -ForegroundColor White
    exit 1
}

