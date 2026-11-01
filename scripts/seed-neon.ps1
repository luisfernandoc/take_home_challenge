$previousDatabaseUrl = $env:DATABASE_URL
$secureDatabaseUrl = Read-Host "Paste the Neon connection URL" -AsSecureString

try {
    $env:DATABASE_URL = [System.Net.NetworkCredential]::new(
        "",
        $secureDatabaseUrl
    ).Password

    uv run --locked python -c "from app.infrastructure.database import database_url; import sys; sys.exit('Expected a Neon database URL') if not (database_url.host or '').endswith('.neon.tech') else None"

    if ($LASTEXITCODE -ne 0) {
        throw "Database destination validation failed."
    }

    uv run --locked python -m scripts.seed

    if ($LASTEXITCODE -ne 0) {
        throw "Seed execution failed."
    }
}
finally {
    if ($null -eq $previousDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $previousDatabaseUrl
    }

    $secureDatabaseUrl.Dispose()
}
