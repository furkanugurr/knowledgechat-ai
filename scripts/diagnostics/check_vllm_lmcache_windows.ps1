[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

function Write-Status {
    param(
        [ValidateSet("PASS", "WARNING", "FAIL")]
        [string]$Level,
        [string]$Message
    )

    $color = switch ($Level) {
        "PASS" { "Green" }
        "WARNING" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

function Invoke-OptionalCommand {
    param(
        [string]$Label,
        [string]$Command,
        [string[]]$Arguments = @()
    )

    $resolved = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $resolved) {
        Write-Status "WARNING" "${Label}: '$Command' is not available."
        return
    }

    Write-Host "`n--- $Label ---"
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
            Write-Status "PASS" "$Label completed."
        } else {
            Write-Status "WARNING" "$Label returned exit code $LASTEXITCODE."
        }
    } catch {
        Write-Status "WARNING" "$Label could not be collected: $($_.Exception.Message)"
    }
}

Write-Host "KnowledgeChat AI - vLLM + LMCache Windows diagnostics"
Write-Host "Read-only collection; no packages or settings are changed."

try {
    $os = Get-CimInstance Win32_OperatingSystem
    Write-Host "`n--- Windows ---"
    Write-Host ("Caption: {0}" -f $os.Caption)
    Write-Host ("Version: {0} (build {1})" -f $os.Version, $os.BuildNumber)
    Write-Host ("Architecture: {0}" -f $os.OSArchitecture)
    Write-Status "PASS" "Windows information collected."
} catch {
    Write-Status "FAIL" "Windows information could not be collected: $($_.Exception.Message)"
}

Write-Host "`n--- PowerShell ---"
Write-Host ("Version: {0}" -f $PSVersionTable.PSVersion)
Write-Status "PASS" "PowerShell information collected."

Invoke-OptionalCommand "WSL status" "wsl.exe" @("--status")
Invoke-OptionalCommand "WSL version" "wsl.exe" @("--version")
Invoke-OptionalCommand "WSL distributions" "wsl.exe" @("--list", "--verbose")
Invoke-OptionalCommand "Docker version" "docker.exe" @("--version")
Invoke-OptionalCommand "Docker Compose version" "docker.exe" @("compose", "version")
Invoke-OptionalCommand "Docker daemon" "docker.exe" @("info", "--format", "Server={{.ServerVersion}}; OS={{.OperatingSystem}}")
Invoke-OptionalCommand "NVIDIA GPU" "nvidia-smi.exe" @("--query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu", "--format=csv,noheader")
Invoke-OptionalCommand "Python version" "python.exe" @("--version")

try {
    $computer = Get-CimInstance Win32_ComputerSystem
    $os = Get-CimInstance Win32_OperatingSystem
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Write-Host "`n--- Capacity ---"
    Write-Host ("RAM total: {0:N2} GB" -f ($computer.TotalPhysicalMemory / 1GB))
    Write-Host ("RAM free: {0:N2} GB" -f ($os.FreePhysicalMemory * 1KB / 1GB))
    Write-Host ("C: free: {0:N2} GB of {1:N2} GB" -f ($disk.FreeSpace / 1GB), ($disk.Size / 1GB))
    Write-Status "PASS" "RAM and disk capacity collected."
} catch {
    Write-Status "WARNING" "RAM or disk capacity could not be collected: $($_.Exception.Message)"
}

$ubuntu = & wsl.exe --list --quiet 2>$null | Where-Object { $_ -match "Ubuntu" }
if ($ubuntu) {
    Write-Status "PASS" "An Ubuntu WSL distribution is available."
} else {
    Write-Status "WARNING" "No Ubuntu WSL distribution was detected."
}

Write-Host "`nDiagnostics complete."
