Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Python virtual environment not found. Please install the project first.'
}

$secureKey = Read-Host 'Enter a NEW DashScope API Key (input is hidden)' -AsSecureString
$keyPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPtr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPtr)
}

$env:OPENAI_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
$env:OPENAI_MODEL = 'qwen3.8-flash'
$env:APP_MODE = 'auto'

Write-Host 'Starting live model mode. The key stays only in this process.'
& '.\.venv\Scripts\python.exe' '.\app.py'
