$ErrorActionPreference = "Stop"

$HostName = "com.chromemcp.nativehost"
$ChromeManifestPath = "$env:APPDATA\Google\Chrome\NativeMessagingHosts\$HostName.json"

if (-not (Test-Path $ChromeManifestPath)) {
    Write-Error "Chrome manifest not found at $ChromeManifestPath. Please install mcp-chrome-bridge first using 'npm install -g mcp-chrome-bridge'."
}

$EdgeRegPath = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName"

Write-Host "Registering $HostName for Microsoft Edge..."

if (-not (Test-Path $EdgeRegPath)) {
    New-Item -Path $EdgeRegPath -Force | Out-Null
}

Set-ItemProperty -Path $EdgeRegPath -Name "(Default)" -Value $ChromeManifestPath

Write-Host "Successfully registered Native Messaging Host for Edge!"
Write-Host "Manifest Path: $ChromeManifestPath"
Write-Host "Registry Key: $EdgeRegPath"
