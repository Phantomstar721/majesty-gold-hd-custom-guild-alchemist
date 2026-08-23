param(
    [string]$SourceRoot = ".\dist\CustomGuildAlchemist",
    [string]$ModsRoot = "$env:USERPROFILE\Documents\My Games\MajestyHD\Mods"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = if ([IO.Path]::IsPathRooted($SourceRoot)) {
    [IO.Path]::GetFullPath($SourceRoot)
} else {
    [IO.Path]::GetFullPath((Join-Path $repoRoot $SourceRoot))
}
$target = [IO.Path]::GetFullPath((Join-Path $ModsRoot "CustomGuildAlchemist"))

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Build output does not exist: $source"
}
if (-not (Test-Path -LiteralPath (Join-Path $source "CustomGuildAlchemist.mmxml") -PathType Leaf)) {
    throw "Build output has no Alchemist manifest: $source"
}
if ($source.Equals($target, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Source and deployment target cannot be the same directory."
}

if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}
New-Item -ItemType Directory -Path $target -Force | Out-Null
Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $target -Recurse -Force

$sourceFiles = Get-ChildItem -LiteralPath $source -File -Recurse
$targetFiles = Get-ChildItem -LiteralPath $target -File -Recurse
if ($sourceFiles.Count -ne $targetFiles.Count) {
    throw "Deployment verification failed: file counts differ."
}
foreach ($sourceFile in $sourceFiles) {
    $relativePath = $sourceFile.FullName.Substring($source.Length).TrimStart('\', '/')
    $targetFile = Join-Path $target $relativePath
    if (-not (Test-Path -LiteralPath $targetFile -PathType Leaf)) {
        throw "Deployment verification failed: missing $relativePath"
    }
    $sourceHash = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) {
        throw "Deployment verification failed: SHA-256 differs for $relativePath"
    }
}
Write-Host "Deployed Custom Guild: Alchemist Lab:"
Write-Host $target
Write-Host "Verified $($sourceFiles.Count) files by SHA-256."
