$ErrorActionPreference = "Stop"

$HostName = "com.chromemcp.nativehost"
$ManifestPath = "$env:APPDATA\Google\Chrome\NativeMessagingHosts\$HostName.json"

if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest file not found at $ManifestPath. Please install mcp-chrome-bridge first."
}

$Manifest = Get-Content $ManifestPath | ConvertFrom-Json

Write-Host "Current Allowed Origins:"
$Manifest.allowed_origins | ForEach-Object { Write-Host " - $_" }

$NewId = Read-Host "Please enter the Chrome Extension ID from chrome://extensions (e.g., jamhCw...)"

if ([string]::IsNullOrWhiteSpace($NewId)) {
    Write-Error "Extension ID cannot be empty."
}

$NewOrigin = "chrome-extension://$NewId/"

if ($Manifest.allowed_origins -contains $NewOrigin) {
    Write-Host "This ID is already registered."
} else {
    $Manifest.allowed_origins += $NewOrigin
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content $ManifestPath
    Write-Host "Successfully added ID: $NewId"
}
