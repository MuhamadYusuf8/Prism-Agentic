# Stop PostgreSQL service
Stop-Service -Name postgresql-x64-16 -Force

# Modify pg_hba.conf to use trust authentication
$pgHba = "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
$content = Get-Content $pgHba
$content = $content -replace 'scram-sha-256', 'trust'
Set-Content -Path $pgHba -Value $content

# Start PostgreSQL service
Start-Service -Name postgresql-x64-16

Write-Output "PostgreSQL reconfigured to trust authentication"
