$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000/api"

Write-Host "1. Fetching Workspace Config for 'demo-spa'..."
$ws = Invoke-RestMethod -Uri "$baseUrl/public/workspace/demo-spa" -Method Get
$service = $ws.services | Where-Object { $_.name -like "*Deep Tissue*" } | Select-Object -First 1

if (-not $service) {
    Write-Error "Service 'Deep Tissue Massage' not found"
}
Write-Host "   Found Service: $($service.name) (ID: $($service.id))"

# Date: Tomorrow
$date = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
Write-Host "2. Checking Availability for $date..."
$slots = Invoke-RestMethod -Uri "$baseUrl/public/services/$($service.id)/availability?date=$date" -Method Get

if ($slots.Count -eq 0) {
    Write-Error "No slots available for $date"
}
$slot = $slots[0]
Write-Host "   Selected Slot: $slot"

# Calculate Start DateTime (Simple concatenation for now, assuming local time match or UTC)
# The API expects ISO format. 
# The slot is HH:MM.
$startDateTime = "${date}T${slot}:00"
Write-Host "   Booking Start: $startDateTime"

Write-Host "3. Creating Booking..."
$body = @{
    service_id = $service.id
    start_datetime = $startDateTime
    name = "Shubham Ragade"
    email = "shubhamragade2014@gmail.com"
    phone = "555-0199"
} | ConvertTo-Json

try {
    $booking = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Post -Body $body -ContentType "application/json"
    Write-Host "   SUCCESS: Booking Created!"
    Write-Host "   ID: $($booking.id)"
    Write-Host "   Status: $($booking.status)"
    Write-Host "   Contact ID: $($booking.contact_id)"
} catch {
    Write-Error "Booking Failed: $_"
    exit 1
}
