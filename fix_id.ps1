$ErrorActionPreference = "Stop"

$HostName = "com.chromemcp.nativehost"
$ManifestPath = "$env:APPDATA\Google\Chrome\NativeMessagingHosts\$HostName.json"

if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest file not found at $ManifestPath. Please install mcp-chrome-bridge first."
}

$Manifest = Get-Content $ManifestPath | ConvertFrom-Json

Write-Host "Current Allowed Origins: $($Manifest.allowed_origins)"

$NewId = Read-Host "Please enter the Extension ID from edge://extensions (e.g., abcdef...)"

if ([string]::IsNullOrWhiteSpace($NewId)) {
    Write-Error "Extension ID cannot be empty."
}

$NewOrigin = "chrome-extension://$NewId/"

if ($Manifest.allowed_origins -contains $NewOrigin) {
    Write-Host "This ID is already allowed."
} else {
    $Manifest.allowed_origins += $NewOrigin
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content $ManifestPath
    Write-Host "Successfully added $NewId to allowed origins."
    Write-Host "Please restart the extension (click reload in edge://extensions) and try connecting again."
}
