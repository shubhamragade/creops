function Get-AuthToken {
    param (
        [string]$Email,
        [string]$Password
    )
    $baseUrl = "http://localhost:8000/api"
    $body = "username=$Email&password=$Password"
    try {
        $token = Invoke-RestMethod -Uri "$baseUrl/login" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
        return $token
    } catch {
        Write-Error "Login failed for $Email : $_"
        throw
    }
}

function Get-OwnerToken {
    return Get-AuthToken -Email "owner@careops.com" -Password "owner123"
}

function Get-StaffToken {
    return Get-AuthToken -Email "staff@careops.com" -Password "staff123"
}
