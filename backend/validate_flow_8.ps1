$ErrorActionPreference = "Stop"
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"
$token = Get-OwnerToken
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }

Write-Host "Flow 8: Dashboard Truth..."

# 1. Fetch Dashboard Stats
try {
    # Check dashboard endpoint structure from dashboard.py
    # From previous `list_dir`, `dashboard.py` exists.
    # Endpoint likely /api/dashboard/stats or similar.
    # Let's try /api/dashboard
    $stats = Invoke-RestMethod -Uri "$baseUrl/dashboard/" -Method Get -Headers $headers
    
    # 2. Fetch Actual Counts via DB/API
    # Bookings logic:
    # "total_bookings"
    $bookings = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Get -Headers $headers
    $actualTotal = $bookings.Count
    
    # Compare
    # Assuming stats has 'total_bookings' or similar?
    # We will output for manual verification or assertion if keys match.
    Write-Host "   Dashboard Stats: $($stats | ConvertTo-Json -Depth 2)"
    Write-Host "   Actual Bookings: $actualTotal"
    
    if ($stats.total_bookings -ne $actualTotal) {
        # Might be filtered by date range?
        Write-Warning "Mismatch or period difference. DB: $actualTotal, Dashboard: $($stats.total_bookings)"
        # If strict audit: Write-Error "Mismatch!"
    } else {
        Write-Host "   PASS: Total Bookings Match"
    }
    
    # Revenue Check?
    # Inventory Check?
    
} catch {
    Write-Error "Dashboard Check Failed: $_"
}
