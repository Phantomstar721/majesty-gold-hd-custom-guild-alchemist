param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [string]$OutputRoot = ".\dist\CustomGuildAlchemistProbe",
    [switch]$IncludePhantomsHauntProbe
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$python = Join-Path $workspaceRoot ".tools\python.cmd"
$builder = Join-Path $repoRoot "src\build_alchemist_probe.py"
$output = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot
} else {
    Join-Path $repoRoot $OutputRoot
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Shared Python launcher was not found: $python"
}
if (-not (Test-Path -LiteralPath $GamePath -PathType Container)) {
    throw "Majesty HD path was not found: $GamePath"
}

$arguments = @(
    $builder,
    "--game-path", $GamePath,
    "--output-root", $output
)
if ($IncludePhantomsHauntProbe) {
    $arguments += "--include-phantoms-haunt-probe"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Alchemist probe build failed with exit code $LASTEXITCODE"
}
