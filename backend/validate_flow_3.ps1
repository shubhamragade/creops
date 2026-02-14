$ErrorActionPreference = "Stop"
. .\auth_helper.ps1

$baseUrl = "http://localhost:8000/api"

Write-Host "1. Owner Login..."
$token = Get-OwnerToken
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }

# Get a booking (using the one from Flow 1 if possible, or list all)
$bookings = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Get -Headers $headers
$booking = $bookings | Select-Object -First 1

if (-not $booking) {
    Write-Error "No bookings found to modify"
}
Write-Host "   Selected Booking ID: $($booking.id) (Status: $($booking.status))"

# 2. Modify Booking (Reschedule)
Write-Host "2. Modifying Booking (Reschedule)..."
# Add 1 hour to start time
$newStart = (Get-Date $booking.start_time).AddHours(1).ToString("yyyy-MM-ddTHH:mm:00")
$body = @{
    start_datetime = $newStart
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/bookings/$($booking.id)" -Method Patch -Body $body -ContentType "application/json" -Headers $headers
    Write-Host "   SUCCESS: Rescheduled to $newStart"
} catch {
    Write-Error "Reschedule Failed: $_"
}

# 3. Cancel Booking
Write-Host "3. Cancelling Booking..."
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/bookings/$($booking.id)/cancel" -Method Post -Headers $headers
    Write-Host "   SUCCESS: Cancelled. Status: $($response.status)"
} catch {
    Write-Error "Cancellation Failed: $_"
}

# 4. Restore Booking
Write-Host "4. Restoring Booking..."
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/bookings/$($booking.id)/restore" -Method Post -Headers $headers
    Write-Host "   SUCCESS: Restored. Status: $($response.status)"
} catch {
    Write-Error "Restore Failed: $_"
}

# 5. Verify Final State
$final = Invoke-RestMethod -Uri "$baseUrl/bookings/" -Method Get -Headers $headers
$b = $final | Where-Object { $_.id -eq $booking.id }
Write-Host "   Final Status: $($b.status)"
if ($b.status -ne "confirmed") {
    Write-Error "Final status mismatch. Expected confirmed, got $($b.status)"
}
