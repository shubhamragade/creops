$ErrorActionPreference = "Continue"

Write-Host "--- Starting Flow 6 & 7 (Persistence & Repeatability) ---"
powershell -ExecutionPolicy Bypass -File validate_flow_6_7.ps1
if ($LASTEXITCODE -ne 0) { Write-Error "Flow 6/7 Failed" }

Write-Host "`n--- Starting Flow 9 (Invalid Requests) ---"
powershell -ExecutionPolicy Bypass -File validate_flow_9.ps1
if ($LASTEXITCODE -ne 0) { Write-Error "Flow 9 Failed" }

Write-Host "`nAll validation scripts completed."
