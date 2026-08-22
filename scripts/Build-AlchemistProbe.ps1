param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [string]$OutputRoot = "",
    [switch]$IncludePhantomsHauntProbe,
    [switch]$UseAP10TitleAliasProbe,
    # The runtime now owns the formerly unsafe AP10 secondary route. Keep the
    # real Brewing control enabled in every normal build; false is retained
    # only for reproducing the pre-runtime diagnostic fixture.
    [switch]$EnableUnsafeBrewingControl = $true,
    [switch]$IncludeSiegeTestFixture,
    [switch]$ApprovedSpriteTestSet,
    [string]$ReuseArtFrom = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$python = Join-Path $workspaceRoot ".tools\python.cmd"
$builder = Join-Path $repoRoot "src\build_alchemist_probe.py"
$effectiveOutputRoot = if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    if ($ApprovedSpriteTestSet) {
        ".\dist\CustomGuildAlchemistSpriteTest"
    } else {
        ".\dist\CustomGuildAlchemistProbe"
    }
} else {
    $OutputRoot
}
$output = if ([IO.Path]::IsPathRooted($effectiveOutputRoot)) {
    $effectiveOutputRoot
} else {
    Join-Path $repoRoot $effectiveOutputRoot
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
# The approved motion gate is a ready-to-run replacement for the established
# two-mod Siege probe.  Its art mode remains independent in the Python builder,
# while this user-facing profile retains the fixture needed to inspect the hero
# immediately and the PHG1 compatibility row needed when Haunt is active first.
$effectiveIncludePhantomsHauntProbe = $IncludePhantomsHauntProbe -or $ApprovedSpriteTestSet
$effectiveIncludeSiegeTestFixture = $IncludeSiegeTestFixture -or $ApprovedSpriteTestSet
if ($effectiveIncludePhantomsHauntProbe) {
    $arguments += "--include-phantoms-haunt-probe"
}
if ($UseAP10TitleAliasProbe) {
    $arguments += "--use-ap10-title-alias-probe"
}
if ($EnableUnsafeBrewingControl) {
    $arguments += "--enable-unsafe-brewing-control"
}
if ($effectiveIncludeSiegeTestFixture) {
    $arguments += "--include-siege-test-fixture"
}
if ($ApprovedSpriteTestSet) {
    $arguments += "--approved-sprite-test-set"
}
$effectiveReuseArtFrom = $ReuseArtFrom
if (-not $ApprovedSpriteTestSet -and [string]::IsNullOrWhiteSpace($effectiveReuseArtFrom)) {
    $effectiveReuseArtFrom = Join-Path $repoRoot "dist\CustomGuildAlchemistSpriteTest"
}
if (-not [string]::IsNullOrWhiteSpace($effectiveReuseArtFrom)) {
    $arguments += "--reuse-art-from"
    $arguments += $effectiveReuseArtFrom
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Alchemist probe build failed with exit code $LASTEXITCODE"
}
