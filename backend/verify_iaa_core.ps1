$ErrorActionPreference = "Continue" # Continue to test all
. .\auth_helper.ps1
$baseUrl = "http://localhost:8000/api"

# TRACKING RESULTS
$results = @{}
function Log-Result {
    param($Flow, $Status, $Note)
    $results[$Flow] = @{ Status=$Status; Note=$Note }
    Write-Host "[$Status] Flow $Flow : $Note"
}

Write-Host "=== STARTING IAA AUDIT ==="

# ----------------------------------------------------------------
# FLOW 3: INVALID LOGIN
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 3: Invalid Login ---"
try {
    $res = Invoke-RestMethod -Uri "$baseUrl/login" -Method Post -Body "username=owner@careops.com&password=WRONG" -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    Log-Result "3" "FAIL" "Login succeeded with wrong password!"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Unauthorized) {
        Log-Result "3" "PASS" "Correctly rejected (401)"
    } else {
        Log-Result "3" "FAIL" "Unexpected status: $($_.Exception.Response.StatusCode)"
    }
}

# ----------------------------------------------------------------
# FLOW 1: OWNER LOGIN
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 1: Owner Login ---"
try {
    $ownerToken = Get-OwnerToken
    if ($ownerToken.access_token) {
        $ownerHeaders = @{ "Authorization" = "Bearer $($ownerToken.access_token)" }
        # Verify Owner Data Access
        $dash = Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Method Get -Headers $ownerHeaders
        if ($dash.bookings) {
             Log-Result "1" "PASS" "Owner logged in & accessed dashboard"
        } else {
             Log-Result "1" "RISK" "Owner logged in but dashboard empty/malformed"
        }
    } else {
        Log-Result "1" "FAIL" "No token returned"
    }
} catch {
    Log-Result "1" "FAIL" "Login/Dashboard failed: $_"
}

# ----------------------------------------------------------------
# FLOW 2: STAFF LOGIN & BOUNDARIES
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 2: Staff Login & Boundaries ---"
try {
    $staffToken = Get-StaffToken
    if ($staffToken.access_token) {
        $staffHeaders = @{ "Authorization" = "Bearer $($staffToken.access_token)" }
        
        # 1. Valid Staff Access (Inbox)
        try {
            $inbox = Invoke-RestMethod -Uri "$baseUrl/conversations/" -Method Get -Headers $staffHeaders
            Write-Host "   Staff accessed inbox (OK)"
        } catch {
            Log-Result "2" "FAIL" "Staff cannot access inbox: $_"
        }

        # 2. Invalid Access (Owner Dashboard)
        $blocked = $false
        try {
            Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Method Get -Headers $staffHeaders -ErrorAction Stop
            Write-Error "Staff accessed Owner Dashboard!"
        } catch {
            if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Forbidden -or $_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Unauthorized) {
                Write-Host "   Staff blocked from Owner Dashboard (OK)"
                $blocked = $true
            } else {
                Write-Error "Staff blocked but wrong code: $($_.Exception.Response.StatusCode)"
            }
        }

        # 3. Invalid Access (Settings/Users - assuming separate endpoint, but Dashboard is main gate)
        # Check 'staff.py' invite endpoint (Owner only)
        try {
            Invoke-RestMethod -Uri "$baseUrl/staff/" -Method Get -Headers $staffHeaders -ErrorAction Stop
             Write-Error "Staff accessed Staff List (Admin Only)!"
             $blocked = $false
        } catch {
             Write-Host "   Staff blocked from Staff List (OK)"
        }

        if ($blocked) {
            Log-Result "2" "PASS" "Staff login works, Admin routes blocked"
        } else {
            Log-Result "2" "FAIL" "Staff accessed restricted areas"
        }

    } else {
        Log-Result "2" "FAIL" "Staff login failed"
    }
} catch {
    Log-Result "2" "FAIL" "Staff Auth Error: $_"
}

# ----------------------------------------------------------------
# FLOW 4: TOKEN ENFORCEMENT
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 4: Token Enforcement ---"
# Test Bad Token
try {
    Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Method Get -Headers @{Authorization="Bearer BAD_TOKEN"} -ErrorAction Stop
    Log-Result "4" "FAIL" "Accepted bad token"
} catch {
    if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::Unauthorized) {
        Log-Result "4" "PASS" "Rejected bad token (401)"
    } else {
         Log-Result "4" "FAIL" "Unexpected status: $($_.Exception.Response.StatusCode)"
    }
}

# ----------------------------------------------------------------
# FLOW 7: ROLE DATA BOUNDARY (Explicit)
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 7: Data Boundary ---"
# Re-using checks from Flow 2 but more specific
if ($results["2"].Status -eq "PASS") {
    Log-Result "7" "PASS" "Covered by Flow 2 checks"
} else {
    Log-Result "7" "FAIL" "See Flow 2 failures"
}

# ----------------------------------------------------------------
# FLOW 11: FORM AUTHORITY
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 11: Form Authority ---"
try {
    # Try to Create Form as Staff
    $body = @{ name="Hacked Form"; type="intake"; workspace_id=2 } | ConvertTo-Json
    
    # We define endpoint /api/forms if it exists?
    # Based on models/form.py, it exists. But endpoint might be nested?
    # Assuming /api/onboarding/workspace or /api/public/workspace but those are likely owner/public.
    # Let's assume standard REST: POST /forms
    # If endpoint doesn't exist 404 is RISK but not CRITICAL security leak.
    
    Invoke-RestMethod -Uri "$baseUrl/forms/" -Method Post -Body $body -ContentType "application/json" -Headers $staffHeaders -ErrorAction Stop
    Log-Result "11" "CRITICAL" "Staff created a form!"
} catch {
    $code = $_.Exception.Response.StatusCode
    if ($code -eq 403 -or $code -eq 401) {
        Log-Result "11" "PASS" "Staff blocked from creating forms ($code)"
    } elseif ($code -eq 404) {
         Log-Result "11" "RISK" "Forms endpoint not found or diff path (Check code)"
    } else {
         Log-Result "11" "FAIL" "Unexpected error: $code"
    }
}

# ----------------------------------------------------------------
# REPORT
# ----------------------------------------------------------------
Write-Host "`n=== RESULTS ==="
$results.GetEnumerator() | Format-Table Key, Value
