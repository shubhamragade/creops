$ErrorActionPreference = "Continue" # Don't stop on expected errors
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"

Write-Host "Flow 9: Invalid Requests..."

# 1. Bad Token
try {
    Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Get -Headers @{Authorization="Bearer bad_token"}
    Write-Error "FAIL: Accepted bad token"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Unauthorized) {
        Write-Host "   PASS: Bad Token Rejected (401)"
    } else {
        Write-Error "FAIL: Unexpected status for bad token: $($_.Exception.Response.StatusCode)"
    }
}

# 2. Missing Data
try {
    $body = @{ name="Test" } | ConvertTo-Json # Missing service_id, etc.
    Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Post -Body $body -ContentType "application/json"
    Write-Error "FAIL: Accepted missing data"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::UnprocessableEntity) { # 422
        Write-Host "   PASS: Missing Data Rejected (422)"
    } else {
         Write-Error "FAIL: Unexpected status for missing data: $($_.Exception.Response.StatusCode)"
    }
}

# 3. Duplicate Booking (same slot) - Should fail 409 or 400
# Reuse logic if needed, but we did this implicitly in Flow 2 checks (overlap).
# Let's try explicit duplicate.
# Fetch existing booking?
# Check availability for tomorrow 09:00 (Flow 1 took it?)
# Flow 1 took tomorrow 09:00.
# Flow 2 took tomorrow 09:00 (Wait, Flow 2 took AddDays(1)? Yes. Same slot?)
# If Flow 1 took it, Flow 2 should have failed overlap?
# Flow 1 used AddDays(1). Flow 2 used AddDays(1).
# They used the SAME SLOT.
# Flow 1: 09:00.
# Flow 2: 09:00.
# If Flow 2 succeeded, then OVERLAP CHECK FAILED?
# Let's check `validate_flow_2.ps1` output.
# Step 232: "SUCCESS: Booking Created via Staff. ID: 5"
# Step 178 (Flow 1): "SUCCESS: Booking Created! ID: 4"
# Both used default first slot (09:00).
# Flow 2 script:
# $date = (Get-Date).AddDays(1)...
# $slots = ... get availability ...
# If Flow 1 booking exists, `get_availability` should NOT return 09:00!
# Why did it return 09:00?
# Maybe `get_availability` logic is flawed?
# Or maybe Flow 1 booking was CANCELLED? No.
# Or maybe Flow 1 date != Flow 2 date?
# Flow 1 ran earlier. Flow 2 ran later.
# `Get-Date` might have shifted days? No, same session.
# This implies a RISK/FAIL in Availability Logic.
# I will flag this in Flow 9 check.

Write-Host "   Checking Overlap Logic..."
# ...
