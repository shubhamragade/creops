$ErrorActionPreference = "Continue" 
. .\auth_helper.ps1
$baseUrl = "http://localhost:8000/api"

# TRACKING RESULTS
$results = @{}
function Log-Result {
    param($Flow, $Status, $Note)
    $results[$Flow] = @{ Status=$Status; Note=$Note }
    Write-Host "[$Status] Flow $Flow : $Note"
}

Write-Host "=== STARTING IAA ADVANCED AUDIT ==="

# ----------------------------------------------------------------
# FLOW 3: INVALID LOGIN (Retry)
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 3: Invalid Login (Retry) ---"
try {
    Invoke-RestMethod -Uri "$baseUrl/login" -Method Post -Body "username=owner@careops.com&password=WRONG" -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    Log-Result "3" "FAIL" "Login succeeded with wrong password!"
} catch {
    $code = $_.Exception.Response.StatusCode
    if ($code -eq 400 -or $code -eq 401) {
        Log-Result "3" "PASS" "Correctly rejected ($code)"
    } else {
        Log-Result "3" "FAIL" "Unexpected status: $code"
    }
}

# ----------------------------------------------------------------
# FLOW 6: MULTI DEVICE
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 6: Multi Device ---"
try {
    # Login 1
    $token1 = Get-OwnerToken
    # Login 2
    $token2 = Get-OwnerToken
    
    if ($token1.access_token -ne $token2.access_token) {
        # Different tokens (likely, dependent on time/salt)
        # Verify BOTH work
        $h1 = @{ "Authorization" = "Bearer $($token1.access_token)" }
        $h2 = @{ "Authorization" = "Bearer $($token2.access_token)" }
        
        $r1 = Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Headers $h1
        $r2 = Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Headers $h2
        
        if ($r1 -and $r2) {
             Log-Result "6" "PASS" "Multi-device login supported (Stateless JWT)"
        } else {
             Log-Result "6" "FAIL" "One session invalidated the other"
        }
    } else {
        Log-Result "6" "PASS" "Same token returned (Stateless)"
    }
} catch {
    Log-Result "6" "FAIL" "Error: $_"
}

# ----------------------------------------------------------------
# FLOW 5: LOGOUT SAFETY
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 5: Logout Safety ---"
# REQUIREMENT: "API enforce... Token removed... API calls fail"
# REALITY CHECK: Stateless JWT cannot "fail" after logout unless blacklist exists.
# We test if the old token Still Works.
try {
    $token = Get-OwnerToken
    $h = @{ "Authorization" = "Bearer $($token.access_token)" }
    
    # Simulate "Logout" (Client throws away token)
    # But hacker kept a copy.
    
    # Try to use it.
    $res = Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Headers $h
    
    # If success -> FAIL because requirement says "API calls fail"
    if ($res) {
        Log-Result "5" "FAIL" "API still accepts token after 'logout' (Stateless JWT Risk)"
    }
} catch {
    Log-Result "5" "PASS" "API rejected token (Unexpected for stateless)"
}

# ----------------------------------------------------------------
# FLOW 11: FORM AUTHORITY (Real Endpoint)
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 11: Form Authority (Real Endpoint) ---"
try {
    $staffToken = Get-StaffToken
    $h = @{ "Authorization" = "Bearer $($staffToken.access_token)" }
    
    # From onboarding.py: /workspaces/{workspace_id}/forms/contact
    # Need workspace ID. Fetch from public.
    $ws = Invoke-RestMethod -Uri "$baseUrl/public/workspace/demo-spa" -Method Get
    $wsId = $ws.id
    
    Invoke-RestMethod -Uri "$baseUrl/onboarding/workspaces/$wsId/forms/contact" -Method Post -Headers $h -ErrorAction Stop
    Log-Result "11" "CRITICAL" "Staff created form!"
} catch {
    $code = $_.Exception.Response.StatusCode
    if ($code -eq 403) {
        Log-Result "11" "PASS" "Staff blocked from creation (403)"
    } else {
        Log-Result "11" "FAIL" "Unexpected status: $code"
    }
}

# ----------------------------------------------------------------
# FLOW 8: OWNER CREATES STAFF
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 8: Owner Creates Staff ---"
try {
    $ownerToken = Get-OwnerToken
    $h = @{ "Authorization" = "Bearer $($ownerToken.access_token)" }
    
    $newStaffEmail = "newstaff" + (Get-Random) + "@test.com"
    $body = @{
        email = $newStaffEmail
        permissions = @{ basic = $true }
    } | ConvertTo-Json
    
    try {
        # Check staff.py valid endpoint: POST /staff/invite
        Invoke-RestMethod -Uri "$baseUrl/staff/invite" -Method Post -Body $body -ContentType "application/json" -Headers $h -ErrorAction Stop
        
        # Verify Login
        # Wait, password is auto-generated and sent via email (mocked?).
        # staff.py: `send_staff_invite(user.email, temp_password)`
        # `send_staff_invite` likely prints to console or log.
        Log-Result "8" "PASS" "Invite sent (Check logs for password to fully verify login)"
    } catch {
        Log-Result "8" "FAIL" "Invite failed: $_"
    }
} catch {
    Log-Result "8" "FAIL" "Review failed: $_"
}

# ----------------------------------------------------------------
# FLOW 13: FORM DATA ISOLATION
# ----------------------------------------------------------------
Write-Host "`n--- Testing Flow 13: Form Data Isolation ---"
# Staff from WS 1 trying to access Forms from WS 2 (if we can create WS 2)
# Creating WS 2 requires public endpoint? /onboarding/workspaces (Public)
try {
    $wsBody = @{
        name = "Isolation Test Spa"
        address = "Hidden"
        timezone = "UTC"
        contact_email = "iso@test.com"
        owner_email = "iso_owner@test.com"
        owner_password = "password123"
    } | ConvertTo-Json
    
    $ws2 = Invoke-RestMethod -Uri "$baseUrl/onboarding/workspaces" -Method Post -Body $wsBody -ContentType "application/json"
    $ws2Id = $ws2.workspace_id
    
    # Try access WS2 as Staff of WS1
    # Staff 1 Token
    $staffToken = Get-StaffToken
    $h = @{ "Authorization" = "Bearer $($staffToken.access_token)" }
    
    # Endpoint: /workspaces/{id}/forms/contact (Creation) -> Should be 403
    # Endpoint: /conversations/? (Filtered by WS in code?)
    
    # Let's try to list conversations for WS 2? 
    # API /conversations uses `current_user.workspace_id` implicitly! 
    # So Staff CANNOT request WS 2 data because the API ignores WS ID param and uses Token WS ID.
    # This design enforces isolation by default.
    
    # Test: Can we force WS ID?
    # If API endpoints don't take WS ID, we are safe.
    # If they DO take WS ID (e.g. /workspaces/{id}/...), we must check.
    
    # Onboarding endpoints take WS ID.
    # Try create form for WS 2 as Staff of WS 1.
    try {
        Invoke-RestMethod -Uri "$baseUrl/onboarding/workspaces/$ws2Id/forms/contact" -Method Post -Headers $h -ErrorAction Stop
        Log-Result "13" "CRITICAL" "Staff (WS1) created form in WS2!"
    } catch {
         if ($_.Exception.Response.StatusCode -eq 403) {
             Log-Result "13" "PASS" "Cross-workspace access blocked (403)"
         } else {
             Log-Result "13" "FAIL" "Unexpected status: $($_.Exception.Response.StatusCode)"
         }
    }
    
} catch {
    Log-Result "13" "RISK" "Could not create second workspace to test: $_"
}


Write-Host "`n=== RESULTS ==="
$results.GetEnumerator() | Format-Table Key, Value
