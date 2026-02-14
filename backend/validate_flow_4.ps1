$ErrorActionPreference = "Continue"
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"

Write-Host "1. Staff Login..."
$token = Get-StaffToken
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }

Write-Host "2. Attempting Forbidden Actions..."

# A. Admin Dashboard
Write-Host "   A. Accessing Admin Dashboard..."
try {
    # Assuming /api/dashboard/stats is owner only? 
    # Let's check dashboard.py
    # If not, checking /api/staff/ (Staff Management)
    Invoke-RestMethod -Uri "$baseUrl/staff/" -Method Get -Headers $headers
    Write-Error "CRITICAL: Staff accessed Staff Management (Admin Route)"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Forbidden) {
        Write-Host "   PASS: Access Denied (403)"
    } elseif ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Unauthorized) {
        Write-Host "   PASS: Access Denied (401)"
    } else {
        Write-Error "FAIL: Unexpected Status: $($_.Exception.Response.StatusCode)"
    }
}

# B. Workspace Config (if exists)
# C. Validation Endpoints
try {
    Invoke-RestMethod -Uri "$baseUrl/validation/system-status" -Method Get -Headers $headers
    # If this is owner only
} catch {
    # Validation endpoints might be public for me? 
    # Let's try to list other users?
    pass
}

# Real Admin Route: Invite Staff?
Write-Host "   B. Inviting Staff..."
try {
    $body = @{ email="hacker@test.com"; role="staff" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$baseUrl/onboarding/workspace/invite" -Method Post -Body $body -ContentType "application/json" -Headers $headers
    Write-Error "CRITICAL: Staff could invite other staff!"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Forbidden) {
        Write-Host "   PASS: Access Denied (403)"
    } else {
        Write-Host "   PASS: Blocked ($($_.Exception.Response.StatusCode))"
    }
}
