$ErrorActionPreference = 'Stop'
$tv4Folder = Split-Path -Parent $MyInvocation.MyCommand.Path
$tv4Python = Join-Path $tv4Folder '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $tv4Python)) {
    py -3.13 -m venv (Join-Path $tv4Folder '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được môi trường Python 3.13.' }
    & $tv4Python -m pip install -r (Join-Path $tv4Folder 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Không cài được dependencies.' }
}
& $tv4Python (Join-Path $tv4Folder 'manage.py') create-demo-users
if ($LASTEXITCODE -ne 0) { throw 'Không khởi tạo được tài khoản demo.' }
& $tv4Python (Join-Path $tv4Folder 'app.py')
