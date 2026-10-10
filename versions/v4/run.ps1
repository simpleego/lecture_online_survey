param([int]$Port = 8003, [switch]$Reload)
$ErrorActionPreference = 'Stop'
$projectPath = $PSScriptRoot
$localPython = Join-Path $projectPath '.venv\Scripts\python.exe'
$previousPython = Join-Path (Split-Path $projectPath -Parent) 'v3\.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $localPython) {
    $pythonPath = $localPython
} elseif (Test-Path -LiteralPath $previousPython) {
    $pythonPath = $previousPython
} else {
    throw 'Create a virtual environment and install requirements.txt first.'
}
Push-Location $projectPath
try {
    $serverArguments = @("-m", "uvicorn", "main:app", "--app-dir", $projectPath, "--port", "$Port")
    if ($Reload) { $serverArguments += "--reload" }
    & $pythonPath @serverArguments
    if ($LASTEXITCODE -ne 0) { throw "Server exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
