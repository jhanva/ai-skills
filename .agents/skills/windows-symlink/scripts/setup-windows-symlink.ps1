[CmdletBinding()]
param(
    [string]$RepoPath = ".",
    [switch]$TryEnableDeveloperMode,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-IsWindowsHost {
    return ($env:OS -eq "Windows_NT")
}

function Test-IsAdmin {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

$actions = @()

if (-not (Test-IsWindowsHost)) {
    throw "This script is intended to run on Windows."
}

if (Test-CommandExists "git") {
    $previous = $null
    try {
        $previous = git config --global core.symlinks 2>$null
    } catch {
        $previous = $null
    }

    git config --global core.symlinks true
    $actions += [ordered]@{
        action = "git_core_symlinks"
        status = "set"
        previous = $previous
        current = "true"
    }
} else {
    $actions += [ordered]@{
        action = "git_core_symlinks"
        status = "skipped"
        reason = "git not found"
    }
}

if ($TryEnableDeveloperMode) {
    if (-not (Test-IsAdmin)) {
        $actions += [ordered]@{
            action = "developer_mode"
            status = "skipped"
            reason = "requires elevated PowerShell session"
        }
    } else {
        try {
            New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Force | Out-Null
            New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name "AllowDevelopmentWithoutDevLicense" -PropertyType DWord -Value 1 -Force | Out-Null
            $actions += [ordered]@{
                action = "developer_mode"
                status = "set"
            }
        } catch {
            $actions += [ordered]@{
                action = "developer_mode"
                status = "failed"
                error = $_.Exception.Message
            }
        }
    }
} else {
    $actions += [ordered]@{
        action = "developer_mode"
        status = "not_requested"
    }
}

$auditScript = Join-Path $PSScriptRoot "audit-windows-symlink.ps1"
$audit = & $auditScript -RepoPath $RepoPath -Json | ConvertFrom-Json

$nextSteps = @()

if ($audit.can_create_symlink -and $audit.git_core_symlinks -eq "true") {
    $nextSteps += "Symlink creation now works in the environment."
}

if ($audit.repo_broken_symlink_count -gt 0) {
    $nextSteps += "The repo checkout still contains broken symlink entries."
    $nextSteps += "Preferred recovery: fresh clone after symlink support is confirmed."
}

if (-not $audit.can_create_symlink) {
    $nextSteps += "If symlink creation still fails, enable Developer Mode from Settings or rerun this script from an elevated PowerShell session with -TryEnableDeveloperMode."
}

$result = [ordered]@{
    actions = $actions
    audit = $audit
    next_steps = $nextSteps
}

if ($Json) {
    $result | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host "## Windows symlink setup"
Write-Host ""
Write-Host "Actions:"
$actions | ForEach-Object {
    if ($_.status -eq "set") {
        Write-Host ("- {0}: {1}" -f $_.action, $_.status)
    } elseif ($_.reason) {
        Write-Host ("- {0}: {1} ({2})" -f $_.action, $_.status, $_.reason)
    } elseif ($_.error) {
        Write-Host ("- {0}: {1} ({2})" -f $_.action, $_.status, $_.error)
    } else {
        Write-Host ("- {0}: {1}" -f $_.action, $_.status)
    }
}

Write-Host ""
Write-Host "Audit summary:"
Write-Host ("- Developer Mode: {0}" -f $audit.developer_mode)
Write-Host ("- git core.symlinks: {0}" -f $audit.git_core_symlinks)
Write-Host ("- Temp symlink test: {0}" -f $audit.can_create_symlink)
Write-Host ("- Broken repo symlinks: {0}" -f $audit.repo_broken_symlink_count)

if ($nextSteps.Count -gt 0) {
    Write-Host ""
    Write-Host "Next steps:"
    $nextSteps | ForEach-Object {
        Write-Host ("- {0}" -f $_)
    }
}
