$ErrorActionPreference = "Stop"

git config core.hooksPath .githooks
Write-Output "Configured .githooks as the repository hooks path."
Write-Output "Commits will be pushed automatically to origin."
