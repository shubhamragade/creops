$ErrorActionPreference = "Stop"
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"
$token = Get-OwnerToken
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }

Write-Host "Flow 6: Checking Persistence..."
$bookings = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Get -Headers $headers
$count = $bookings.Count
Write-Host "   found $count bookings."
if ($count -eq 0) {
    Write-Error "FAIL: No bookings found after restart!"
    exit 1
}
Write-Host "   PASS: Data persisted."

Write-Host "Flow 7: Repeatability (Create/Cancel Loop)..."
# 3 Iterations
$ws = Invoke-RestMethod -Uri "$baseUrl/public/workspace/demo-spa" -Method Get
$service = $ws.services | Select-Object -First 1

for ($i=1; $i -le 3; $i++) {
    Write-Host "   Iteration $i..."
    # 1. Create
    # Use different times or random
    $date = (Get-Date).AddDays(4).ToString("yyyy-MM-dd")
    $time = "1${i}:00" # 11:00, 12:00, 13:00
    $start = "${date}T${time}:00"
    
    $body = @{
        service_id = $service.id
        start_datetime = $start
        name = "Loop User $i"
        email = "loop$i@test.com"
        phone = "555-999$i"
    } | ConvertTo-Json
    
    try {
        $b = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Post -Body $body -ContentType "application/json"
        Write-Host "      Created ID: $($b.id)"
    } catch {
        Write-Error "      Create Failed: $_"
        continue
    }
    
    # 2. Cancel
    try {
        Invoke-RestMethod -Uri "$baseUrl/bookings/$($b.id)/cancel" -Method Post -Headers $headers | Out-Null
        Write-Host "      Cancelled ID: $($b.id)"
    } catch {
         Write-Error "      Cancel Failed: $_"
    }

    # 3. Restore
    try {
         Invoke-RestMethod -Uri "$baseUrl/bookings/$($b.id)/restore" -Method Post -Headers $headers | Out-Null
         Write-Host "      Restored ID: $($b.id)"
    } catch {
          Write-Error "      Restore Failed: $_"
    }
}
Write-Host "   PASS: Repeatability Loop Complete"
