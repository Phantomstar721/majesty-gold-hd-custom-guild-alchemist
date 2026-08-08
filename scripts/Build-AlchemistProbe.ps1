param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [string]$OutputRoot = ".\dist\CustomGuildAlchemistProbe",
    [switch]$IncludePhantomsHauntProbe,
    [switch]$UseAP10TitleAliasProbe,
    # The runtime now owns the formerly unsafe AP10 secondary route. Keep the
    # real Brewing control enabled in every normal build; false is retained
    # only for reproducing the pre-runtime diagnostic fixture.
    [switch]$EnableUnsafeBrewingControl = $true,
    [switch]$IncludeSiegeTestFixture
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
if ($UseAP10TitleAliasProbe) {
    $arguments += "--use-ap10-title-alias-probe"
}
if ($EnableUnsafeBrewingControl) {
    $arguments += "--enable-unsafe-brewing-control"
}
if ($IncludeSiegeTestFixture) {
    $arguments += "--include-siege-test-fixture"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Alchemist probe build failed with exit code $LASTEXITCODE"
}
