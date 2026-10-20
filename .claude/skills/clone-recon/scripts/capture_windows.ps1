<#
capture_windows.ps1 - Captura una ventana de Windows via UI Automation. Sin instalar nada.

Guarda <Out>\<Id>.raw.json (arbol UIA crudo) y <Out>\<Id>.png (la ventana).
Normalizar despues con:
  python uitree.py normalize --from uia <Out>\<Id>.raw.json --out <Out>\<Id>.tree.json --screen <Id>

Uso:
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Process notepad
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Title "Calculadora"

Exit: 0 ok, 2 ventana no encontrada o acceso denegado.
#>
param(
    [Parameter(Mandatory = $true)][string]$Id,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Process = "",
    [string]$Title = "",
    [int]$MaxDepth = 25
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$script:Truncated = $false

function Fail([string]$Message) {
    [Console]::Error.WriteLine("capture_windows: $Message")
    exit 2
}

function Find-Window {
    if (-not $Process -and -not $Title) { Fail "indica -Process o -Title." }
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = [System.Windows.Automation.Condition]::TrueCondition
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
    $found = @()
    foreach ($w in $windows) {
        $info = $w.Current
        if ($Title -and $info.Name -notlike "*$Title*") { continue }
        if ($Process) {
            try { $procName = (Get-Process -Id $info.ProcessId).ProcessName } catch { continue }
            if ($procName -ne $Process) { continue }
        }
        $found += $w
    }
    if ($found.Count -eq 0) {
        $hint = ""
        if ($Process) { $hint = " Si es una app de la Tienda (UWP/WinUI) vive dentro de ApplicationFrameHost: usa -Title." }
        Fail "ventana no encontrada.$hint"
    }
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    foreach ($w in $found) {
        if ($focused -and $focused.Current.ProcessId -eq $w.Current.ProcessId) { return $w }
    }
    if ($found.Count -gt 1) {
        [Console]::Error.WriteLine("capture_windows: $($found.Count) ventanas coinciden; uso '$($found[0].Current.Name)'.")
    }
    return $found[0]
}

function Get-Rect($element) {
    $r = $element.Current.BoundingRectangle
    if ($r.IsEmpty) { return @(0, 0, 0, 0) }
    return @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height)
}

function Get-PatternValue($element) {
    $pattern = $null
    if ($element.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {
        return $pattern.Current.Value
    }
    return $null
}

function Get-ToggleState($element) {
    $pattern = $null
    if ($element.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$pattern)) {
        return [string]$pattern.Current.ToggleState
    }
    return $null
}

function Convert-Node($element, [int]$depth) {
    $info = $element.Current
    $node = [ordered]@{
        type         = $info.ControlType.ProgrammaticName -replace '^ControlType\.', ''
        name         = $info.Name
        automationId = $info.AutomationId
        className    = $info.ClassName
        rect         = Get-Rect $element
        enabled      = $info.IsEnabled
        offscreen    = $info.IsOffscreen
        value        = Get-PatternValue $element
        toggle       = Get-ToggleState $element
        children     = @()
    }
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $child = $walker.GetFirstChild($element)
    if ($child -and $depth -ge $MaxDepth) {
        $script:Truncated = $true
        return $node
    }
    $kids = New-Object System.Collections.ArrayList
    while ($child) {
        [void]$kids.Add((Convert-Node $child ($depth + 1)))
        $child = $walker.GetNextSibling($child)
    }
    $node.children = $kids.ToArray()
    return $node
}

$window = Find-Window
try {
    $tree = Convert-Node $window 0
} catch [System.UnauthorizedAccessException] {
    Fail "acceso denegado. La app corre como administrador: ejecuta la terminal como administrador o captura solo screenshot."
} catch [System.Windows.Automation.ElementNotAvailableException] {
    Fail "la ventana se cerro durante la captura."
}

$rect = Get-Rect $window
$procName = (Get-Process -Id $window.Current.ProcessId).ProcessName
$raw = [ordered]@{
    window    = [ordered]@{ title = $window.Current.Name; process = $procName; rect = $rect }
    truncated = $script:Truncated
    root      = $tree
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$base = Join-Path $Out $Id
$json = $raw | ConvertTo-Json -Depth 100 -Compress
[System.IO.File]::WriteAllText("$base.raw.json", $json, (New-Object System.Text.UTF8Encoding($false)))

if ($rect[2] -gt 0 -and $rect[3] -gt 0) {
    $bitmap = New-Object System.Drawing.Bitmap($rect[2], $rect[3])
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($rect[0], $rect[1], 0, 0, $bitmap.Size)
    $bitmap.Save("$base.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

Write-Output "ok: $base.raw.json ($procName, '$($window.Current.Name)', truncated=$($script:Truncated))"
exit 0
