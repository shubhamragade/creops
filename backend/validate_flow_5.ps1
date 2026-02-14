$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000/api"

Write-Host "1. Fetching Service..."
$ws = Invoke-RestMethod -Uri "$baseUrl/public/workspace/demo-spa" -Method Get
$service = $ws.services | Select-Object -First 1

# Find a slot
$date = (Get-Date).AddDays(4).ToString("yyyy-MM-dd") # Monday
$slots = Invoke-RestMethod -Uri "$baseUrl/public/services/$($service.id)/availability?date=$date" -Method Get
if ($slots.Count -eq 0) {
    Write-Error "No slots available for Flow 5 test"
}
$slot = $slots[0]
$startDateTime = "${date}T${slot}:00"

Write-Host "2. Creating Booking (Expect Success)..."
$body = @{
    service_id = $service.id
    start_datetime = $startDateTime
    name = "No Email User"
    email = "noemail@validation.com"
    phone = "555-0000"
} | ConvertTo-Json

try {
    $booking = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Post -Body $body -ContentType "application/json"
    Write-Host "   SUCCESS: Booking Created. ID: $($booking.id)"
    Write-Host "   Status: $($booking.status)"
} catch {
    Write-Error "Booking Failed (CRITICAL): $_"
    exit 1
}

# 3. Verify Logs (Manual or via API if exposure exists)
Write-Host "3. Please check server logs for 'Email delivery failed' message."
