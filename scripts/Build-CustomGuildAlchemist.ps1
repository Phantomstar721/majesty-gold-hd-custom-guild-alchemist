param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [string]$OutputRoot = "",
    [switch]$IncludePhantomsHauntCompatibility,
    [switch]$IncludeSiegeTestFixture,
    [switch]$ApprovedSpriteTestSet,
    [string]$ReuseArtFrom = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$python = Join-Path $workspaceRoot ".tools\python.cmd"
$builder = Join-Path $repoRoot "src\build_custom_guild_alchemist.py"
$effectiveOutputRoot = if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    if ($ApprovedSpriteTestSet) {
        ".\dist\CustomGuildAlchemistSpriteTest"
    } else {
        ".\dist\CustomGuildAlchemist"
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
# two-mod Siege fixture. Its art mode remains independent in the Python builder,
# while this user-facing profile retains the fixture needed to inspect the hero
# immediately and the PHG1 compatibility row needed when Haunt is active first.
$effectiveIncludePhantomsHauntCompatibility = $IncludePhantomsHauntCompatibility -or $ApprovedSpriteTestSet
$effectiveIncludeSiegeTestFixture = $IncludeSiegeTestFixture -or $ApprovedSpriteTestSet
if ($effectiveIncludePhantomsHauntCompatibility) {
    $arguments += "--include-phantoms-haunt-compatibility"
}
$arguments += "--enable-brewing-control"
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
    throw "Alchemist package build failed with exit code $LASTEXITCODE"
}
