# Move to the repository root (parent of this script's folder) and run manage.py
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    # Try to auto-activate a venv if one exists in the project root
    $venvCandidates = @('venv', '.venv', 'env')
    foreach ($v in $venvCandidates) {
        $activate = Join-Path $Root "$v\Scripts\Activate.ps1"
        if (Test-Path $activate) {
            # Dot-source so activation affects this session
            . $activate
            break
        }
    }

    # Forward any arguments passed to this script to manage.py
    $argString = $args -join ' '

    if ($argString) {
        & py manage.py runserver $argString
    } else {
        & py manage.py runserver
    }
} finally {
    Pop-Location
}
