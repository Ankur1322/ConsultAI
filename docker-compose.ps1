$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

if (-not (Test-Path $docker)) {
    throw "Docker Desktop is not installed at $docker"
}

& $docker compose @args
exit $LASTEXITCODE
