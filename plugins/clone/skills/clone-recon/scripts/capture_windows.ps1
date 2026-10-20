<#
capture_windows.ps1 - Captura una ventana de Windows via UI Automation. Sin instalar nada.

Guarda <Out>\<Id>.raw.json (arbol UIA crudo) y <Out>\<Id>.png (la ventana).
Normalizar despues con:
  python uitree.py normalize --from uia <Out>\<Id>.raw.json --out <Out>\<Id>.tree.json --screen <Id>

Uso:
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Process notepad
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Title "Calculadora"

Si la ventana no muestra controles visibles (recien abierta, minimizada, en
otro escritorio) reintenta -Retries veces con 500 ms de espera.

Exit: 0 ok, 1 captura parcial (sin controles visibles), 2 ventana no encontrada o acceso denegado.
#>
param(
    [Parameter(Mandatory = $true)][string]$Id,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Process = "",
    [string]$Title = "",
    [int]$MaxDepth = 25,
    [int]$Retries = 3
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

function Test-VisibleChild($node) {
    foreach ($child in $node.children) {
        if (-not $child.offscreen -and $child.rect[2] -gt 0 -and $child.rect[3] -gt 0) { return $true }
    }
    return $false
}

$window = Find-Window
for ($attempt = 1; $attempt -le $Retries; $attempt++) {
    $script:Truncated = $false
    try {
        $tree = Convert-Node $window 0
    } catch [System.UnauthorizedAccessException] {
        Fail "acceso denegado. La app corre como administrador: ejecuta la terminal como administrador o captura solo screenshot."
    } catch [System.Windows.Automation.ElementNotAvailableException] {
        Fail "la ventana se cerro durante la captura."
    }
    if (Test-VisibleChild $tree) { break }
    if ($attempt -lt $Retries) {
        [Console]::Error.WriteLine("capture_windows: la ventana no muestra controles visibles; reintento $attempt/$($Retries - 1) en 500 ms.")
        Start-Sleep -Milliseconds 500
    }
}
$partial = -not (Test-VisibleChild $tree)

$rect = Get-Rect $window
if ($partial) {
    $why = "ventana oculta, en otro escritorio o aun cargando"
    if ($rect[0] -le -32000) { $why = "la ventana esta minimizada: restaurala y repite" }
    [Console]::Error.WriteLine("capture_windows: sin controles visibles tras $Retries intentos ($why). Se guarda igual; la pantalla queda como solo features.")
}
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
if ($partial) { exit 1 }
exit 0
