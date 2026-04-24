[CmdletBinding()]
param(
    [string]$RepoPath = ".",
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

if (-not (Test-IsWindowsHost)) {
    throw "This script is intended to run on Windows."
}

function Get-DeveloperModeState {
    try {
        $props = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -ErrorAction Stop
        if ($null -ne $props.AllowDevelopmentWithoutDevLicense) {
            return [int]$props.AllowDevelopmentWithoutDevLicense
        }
        return 0
    } catch {
        return 0
    }
}

function Get-FilesystemInfo {
    param([string]$Path)

    try {
        $resolved = (Resolve-Path -LiteralPath $Path).Path
        $root = [System.IO.Path]::GetPathRoot($resolved)
        $drive = $root.TrimEnd("\")
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$drive'" -ErrorAction Stop
        return [ordered]@{
            root = $root
            filesystem = $disk.FileSystem
        }
    } catch {
        return [ordered]@{
            root = $null
            filesystem = $null
            error = $_.Exception.Message
        }
    }
}

function Test-SymlinkCreate {
    $tempBase = Join-Path $env:TEMP ("symlink-test-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempBase | Out-Null

    try {
        $target = Join-Path $tempBase "target.txt"
        $link = Join-Path $tempBase "link.txt"
        Set-Content -LiteralPath $target -Value "ok" -NoNewline
        New-Item -ItemType SymbolicLink -Path $link -Target $target | Out-Null

        $item = Get-Item -LiteralPath $link -Force
        return [ordered]@{
            ok = $true
            link_type = $item.LinkType
            target = $item.Target
        }
    } catch {
        return [ordered]@{
            ok = $false
            error = $_.Exception.Message
        }
    } finally {
        Remove-Item -LiteralPath $tempBase -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Test-IsGitWorkTree {
    param([string]$Path)

    if (-not (Test-CommandExists "git")) {
        return $false
    }

    try {
        $value = git -C $Path rev-parse --is-inside-work-tree 2>$null
        return ($LASTEXITCODE -eq 0 -and $value -eq "true")
    } catch {
        return $false
    }
}

function Get-GitConfigValue {
    param(
        [string]$Scope,
        [string]$Key
    )

    try {
        $value = git config $Scope $Key 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $value
        }
        return $null
    } catch {
        return $null
    }
}

function Get-RepoGitConfigValue {
    param(
        [string]$Path,
        [string]$Scope,
        [string]$Key
    )

    try {
        $args = @("-C", $Path, "config")
        if ($Scope) {
            $args += $Scope
        }
        $args += @("--get", $Key)
        $value = & git @args 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $value
        }
        return $null
    } catch {
        return $null
    }
}

function Get-RepoSymlinkStatus {
    param([string]$Path)

    if (-not (Test-IsGitWorkTree $Path)) {
        return @()
    }

    $result = @()
    $lines = git -C $Path ls-files -s 2>$null
    foreach ($line in $lines) {
        if ($line -match '^120000\s+[0-9a-f]+\s+\d+\t(.+)$') {
            $rel = $Matches[1]
            $abs = Join-Path $Path $rel
            $state = "missing"
            $detail = $null

            if (Test-Path -LiteralPath $abs) {
                $item = Get-Item -LiteralPath $abs -Force
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    $state = "symlink"
                    $detail = $item.LinkType
                } else {
                    $state = "plain_file"
                    try {
                        $raw = Get-Content -LiteralPath $abs -Raw -ErrorAction Stop
                        if ($raw.Length -le 260) {
                            $detail = $raw.Trim()
                        }
                    } catch {
                        $detail = "unreadable"
                    }
                }
            }

            $result += [ordered]@{
                path = $rel
                state = $state
                detail = $detail
            }
        }
    }

    return $result
}

$repoResolved = try { (Resolve-Path -LiteralPath $RepoPath).Path } catch { $RepoPath }
$fsInfo = Get-FilesystemInfo -Path $RepoPath
$developerMode = Get-DeveloperModeState
$symlinkTest = Test-SymlinkCreate
$repoIsGit = (Test-IsGitWorkTree $RepoPath)
$repoEntries = Get-RepoSymlinkStatus -Path $RepoPath
$brokenEntries = @($repoEntries | Where-Object { $_.state -ne "symlink" })
$gitCoreSymlinksGlobal = if (Test-CommandExists "git") { (Get-GitConfigValue -Scope "--global" -Key "core.symlinks") } else { $null }
$gitCoreSymlinksLocal = if ($repoIsGit) { (Get-RepoGitConfigValue -Path $RepoPath -Scope "--local" -Key "core.symlinks") } else { $null }
$gitCoreSymlinksEffective = if ($repoIsGit) { (Get-RepoGitConfigValue -Path $RepoPath -Scope $null -Key "core.symlinks") } else { $gitCoreSymlinksGlobal }

$result = [ordered]@{
    os = "Windows"
    repo_path = $repoResolved
    powershell_version = $PSVersionTable.PSVersion.ToString()
    git_found = (Test-CommandExists "git")
    git_version = if (Test-CommandExists "git") { (git --version) } else { $null }
    is_admin = (Test-IsAdmin)
    developer_mode = ($developerMode -eq 1)
    filesystem = $fsInfo
    git_core_symlinks = $gitCoreSymlinksEffective
    git_core_symlinks_global = $gitCoreSymlinksGlobal
    git_core_symlinks_local = $gitCoreSymlinksLocal
    can_create_symlink = [bool]$symlinkTest.ok
    symlink_test = $symlinkTest
    repo_is_git = $repoIsGit
    repo_symlink_count = $repoEntries.Count
    repo_broken_symlink_count = $brokenEntries.Count
    repo_symlink_entries = $repoEntries
    recommendations = @()
}

if (-not $result.git_found) {
    $result.recommendations += "Install Git for Windows before attempting symlink setup."
}

if ($result.git_core_symlinks_global -ne "true") {
    $result.recommendations += "Run: git config --global core.symlinks true"
}

if ($result.repo_is_git -and $result.git_core_symlinks_local -and $result.git_core_symlinks_local -ne "true") {
    $result.recommendations += ("Repo override detected. Run: git -C `"{0}`" config --local core.symlinks true" -f $result.repo_path)
}

if ($result.repo_is_git -and $result.git_core_symlinks -ne "true") {
    $result.recommendations += "The effective core.symlinks value for this repo is not true. Fix the repo override before re-checkout."
}

if (-not $result.can_create_symlink) {
    if (-not $result.developer_mode) {
        $result.recommendations += "Enable Windows Developer Mode or run the shell as Administrator."
    } else {
        $result.recommendations += "If Developer Mode is already enabled, retry from an elevated shell and validate the filesystem."
    }
}

if ($result.repo_broken_symlink_count -gt 0) {
    $result.recommendations += "This checkout contains broken symlink entries. After enabling symlink support, prefer a fresh clone or a clean re-checkout."
}

if ($Json) {
    $result | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host "## Windows symlink audit"
Write-Host ""
Write-Host ("OS:                  {0}" -f $result.os)
Write-Host ("Repo path:           {0}" -f $result.repo_path)
Write-Host ("PowerShell:          {0}" -f $result.powershell_version)
Write-Host ("Git found:           {0}" -f $result.git_found)
Write-Host ("Git version:         {0}" -f $result.git_version)
Write-Host ("Admin:               {0}" -f $result.is_admin)
Write-Host ("Developer Mode:      {0}" -f $result.developer_mode)
Write-Host ("Filesystem:          {0}" -f $result.filesystem.filesystem)
Write-Host ("git core.symlinks:   {0}" -f $result.git_core_symlinks)
Write-Host ("global core.symlinks:{0}" -f $result.git_core_symlinks_global)
Write-Host ("local core.symlinks: {0}" -f $result.git_core_symlinks_local)
Write-Host ("Temp symlink test:   {0}" -f $result.can_create_symlink)
Write-Host ("Repo symlink count:  {0}" -f $result.repo_symlink_count)
Write-Host ("Broken in checkout:  {0}" -f $result.repo_broken_symlink_count)

if ($result.repo_broken_symlink_count -gt 0) {
    Write-Host ""
    Write-Host "Broken entries:"
    $brokenEntries | Select-Object -First 10 | ForEach-Object {
        Write-Host ("- {0} [{1}] {2}" -f $_.path, $_.state, $_.detail)
    }
}

if ($result.recommendations.Count -gt 0) {
    Write-Host ""
    Write-Host "Recommendations:"
    $result.recommendations | ForEach-Object {
        Write-Host ("- {0}" -f $_)
    }
}
