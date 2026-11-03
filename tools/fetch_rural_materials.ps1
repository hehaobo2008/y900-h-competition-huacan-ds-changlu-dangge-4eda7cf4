$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$ids = @('dirt', 'fine_grained_wood', 'white_plaster_rough_01', 'rough_linen', 'clay_roof_tiles')
$maps = @('Diffuse', 'nor_gl', 'Rough')
$manifest = @()
foreach ($id in $ids) {
  $assetDir = Join-Path $root "assets/materials/polyhaven/$id"
  New-Item -ItemType Directory -Path $assetDir -Force | Out-Null
  $files = Invoke-RestMethod -Uri "https://api.polyhaven.com/files/$id" -TimeoutSec 30
  foreach ($map in $maps) {
    $entry = $files.$map.'1k'.jpg
    if (-not $entry) { throw "No 1k JPG for $id / $map" }
    $target = Join-Path $assetDir "$map.jpg"
    if (-not (Test-Path -LiteralPath $target) -or (Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLower() -ne $entry.md5) {
      Invoke-WebRequest -Uri $entry.url -OutFile $target -TimeoutSec 120
    }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLower()
    if ($actual -ne $entry.md5) { throw "Hash mismatch for $target" }
    $manifest += [PSCustomObject]@{asset=$id; map=$map; path="assets/materials/polyhaven/$id/$map.jpg"; md5=$actual; source=$entry.url; license='CC0 1.0'}
    Write-Output "$id / $map verified"
  }
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'assets/materials/polyhaven/manifest.json') -Encoding utf8
