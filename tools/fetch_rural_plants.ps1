$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$ids = @('grass_bermuda_01', 'weed_plant_02')
$manifest = @()
foreach ($id in $ids) {
  $base = Join-Path $root "assets/vegetation/source/$id"
  New-Item -ItemType Directory -Path $base -Force | Out-Null
  $files = Invoke-RestMethod -Uri "https://api.polyhaven.com/files/$id" -TimeoutSec 30
  $model = $files.gltf.'1k'.gltf
  $items = @([PSCustomObject]@{name="$id.gltf"; metadata=$model})
  $items += [PSCustomObject]@{name='alpha.png'; metadata=$files.Alpha.'1k'.png}
  foreach ($prop in $model.include.PSObject.Properties) {
    $items += [PSCustomObject]@{name=$prop.Name; metadata=$prop.Value}
  }
  foreach ($item in $items) {
    $target = Join-Path $base $item.name
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $target) -or (Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLower() -ne $item.metadata.md5) {
      Invoke-WebRequest -Uri $item.metadata.url -OutFile $target -TimeoutSec 120
    }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLower()
    if ($actual -ne $item.metadata.md5) { throw "Hash mismatch for $target" }
    $manifest += [PSCustomObject]@{asset=$id; file=$item.name; md5=$actual; source=$item.metadata.url; license='CC0 1.0'}
  }
  & (Join-Path $root 'node_modules/.bin/gltf-transform.cmd') copy (Join-Path $base "$id.gltf") (Join-Path $root "assets/vegetation/$id.glb")
  if ($LASTEXITCODE -ne 0) { throw "Could not package $id" }
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'assets/vegetation/source/manifest.json') -Encoding utf8
& python (Join-Path $root 'tools/prepare_rural_plants.py')
if ($LASTEXITCODE -ne 0) { throw 'Could not prepare plant alpha maps' }
& node (Join-Path $root 'tools/pack_rural_plants.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Could not pack plant alpha maps' }
