$ErrorActionPreference = "Stop"

$folder = Join-Path ([Environment]::GetFolderPath("Desktop")) "Flight_Delay_2025"
$account = "stflight60106354"
$container = "raw"
$prefix = "flight_delays/2025/v1"

$manifest = Import-Csv (Join-Path $folder "manifest.csv")
$files = @($manifest.file_name) + @("manifest.csv")

$log = Join-Path $folder ("ingestion_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".txt")
Start-Transcript -Path $log

try {
    foreach ($name in $files) {
        $local = Join-Path $folder $name
        $blob = "$prefix/$name"

        if (!(Test-Path -LiteralPath $local)) {
            throw "Local file missing: $name"
        }

        $expected = (Get-Item -LiteralPath $local).Length

        if ($name -ne "manifest.csv") {
            $row = $manifest | Where-Object { $_.file_name -eq $name }

            if ($expected -ne [long]$row.size_bytes) {
                throw "Local size differs from manifest: $name"
            }

            $hash = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash
            if ($hash -ne $row.sha256) {
                throw "Local hash differs from manifest: $name"
            }
        }

        $exists = az storage blob exists `
            --account-name $account `
            --container-name $container `
            --name $blob `
            --auth-mode key `
            --query exists -o tsv --only-show-errors

        if ($LASTEXITCODE -ne 0) {
            throw "Could not check Azure file: $name"
        }

        if ($exists -eq "true") {
            $remoteSize = az storage blob show `
                --account-name $account `
                --container-name $container `
                --name $blob `
                --auth-mode key `
                --query properties.contentLength -o tsv --only-show-errors

            if ($LASTEXITCODE -ne 0) {
                throw "Could not read Azure file: $name"
            }

            if ([long]$remoteSize -ne $expected) {
                throw "STOP: Existing Azure file size differs: $name"
            }

            Write-Host "SKIPPED (already exists): $name" -ForegroundColor Green
        }
        else {
            az storage blob upload `
                --account-name $account `
                --container-name $container `
                --name $blob `
                --file $local `
                --auth-mode key `
                --overwrite false `
                --only-show-errors -o none

            if ($LASTEXITCODE -ne 0) {
                throw "Upload failed: $name"
            }

            Write-Host "UPLOADED: $name" -ForegroundColor Cyan
        }
    }

    Write-Host "SAFE INGESTION COMPLETED" -ForegroundColor Green
}
finally {
    Stop-Transcript
}

Write-Host "Log saved: $log"
