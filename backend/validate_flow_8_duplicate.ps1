$ErrorActionPreference = "Stop"
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"

Write-Host "Flow 8: Duplicate / Spam Actions..."
# 1. Fetch Service & Slot
$ws = Invoke-RestMethod -Uri "$baseUrl/public/workspace/demo-spa" -Method Get
$service = $ws.services | Select-Object -First 1

$date = (Get-Date).AddDays(5).ToString("yyyy-MM-dd") # Far future to avoid conflict
$slots = Invoke-RestMethod -Uri "$baseUrl/public/services/$($service.id)/availability?date=$date" -Method Get
if ($slots.Count -eq 0) { Write-Error "No slots available"; exit 1 }
$slot = $slots[0]
$startDateTime = "${date}T${slot}:00"

Write-Host "   Targeting Slot: $startDateTime"

# 2. Prepare Booking Body
$body = @{
    service_id = $service.id
    start_datetime = $startDateTime
    name = "Spammer User"
    email = "spam@test.com"
    phone = "555-9999"
} | ConvertTo-Json

# 3. Launch Parallel Jobs
$scriptBlock = {
    param($url, $b)
    try {
        $res = Invoke-RestMethod -Uri "$url/bookings/" -Method Post -Body $b -ContentType "application/json"
        return "SUCCESS: $($res.id)"
    } catch {
        return "FAIL: $($_.Exception.Response.StatusCode)"
    }
}

Write-Host "   Launching 5 rapid requests..."
$jobs = @()
for ($i=1; $i -le 5; $i++) {
    $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $baseUrl, $body
}

Write-Host "   Waiting for jobs..."
$results = Receive-Job -Job $jobs -Wait

Write-Host "   Results:"
$results | ForEach-Object { Write-Host "      $_" }

# 4. Verify Count
$successCount = ($results | Where-Object { $_ -like "SUCCESS*" }).Count
Write-Host "   Successful Bookings: $successCount"

if ($successCount -gt 1) {
    Write-Error "CRITICAL: Multiple bookings processed for same slot!"
} else {
    Write-Host "   PASS: Only one booking succeeded."
}
