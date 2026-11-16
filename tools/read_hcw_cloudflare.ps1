param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference='Stop'
$hcwProject=Get-Content -LiteralPath 'L:/harmonyprojectdevelopment/HCW/test/out/45113_cloudflare_project.json' -Raw | ConvertFrom-Json
if($hcwProject.name -ne 'web' -or $hcwProject.domains -notcontains 'harmonyconnectwindows.com'){throw 'Unexpected website'}
$hcwSecure=Get-Content -LiteralPath (Join-Path $env:USERPROFILE '.codex/private/hcw-cloudflare-token.dpapi') | ConvertTo-SecureString
$hcwCredential=New-Object System.Management.Automation.PSCredential('token',$hcwSecure)
try{
 $hcwHeaders=@{Authorization=('Bearer '+$hcwCredential.GetNetworkCredential().Password)}
 $hcwBase="https://api.cloudflare.com/client/v4/accounts/$($hcwProject.accountId)/pages/projects/web"
 $hcwResponse=Invoke-RestMethod -Uri $hcwBase -Headers $hcwHeaders -TimeoutSec 45
 if(-not $hcwResponse.success){throw 'Cannot read production website'}
 $hcwLive=$hcwResponse.result
 $hcwFiles=Invoke-RestMethod -Uri "$hcwBase/deployments/$($hcwLive.canonical_deployment.id)/files" -Headers $hcwHeaders -TimeoutSec 45
 if(-not $hcwFiles.success){throw 'Cannot read deployed files'}
 New-Item -ItemType Directory -Force -Path $Destination | Out-Null
 $hcwSummary=[ordered]@{name=$hcwLive.name;domains=$hcwLive.domains;production_branch=$hcwLive.production_branch;deployment=$hcwLive.canonical_deployment.id;url=$hcwLive.canonical_deployment.url;created_on=$hcwLive.canonical_deployment.created_on;stage=$hcwLive.canonical_deployment.latest_stage}
 [IO.File]::WriteAllText((Join-Path $Destination 'production-live.json'),($hcwSummary | ConvertTo-Json -Depth 12))
 [IO.File]::WriteAllText((Join-Path $Destination 'production-files-live.json'),($hcwFiles.result | ConvertTo-Json -Depth 12))
 [pscustomobject]@{project=$hcwLive.name;deployment=$hcwLive.canonical_deployment.id;files=@($hcwFiles.result.files.PSObject.Properties).Count;destination=$Destination} | ConvertTo-Json -Compress
}finally{Remove-Variable hcwSecure,hcwCredential,hcwHeaders -ErrorAction SilentlyContinue}
