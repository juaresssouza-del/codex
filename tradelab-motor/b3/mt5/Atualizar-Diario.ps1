param(
    [Parameter(Mandatory=$true)][string]$Arquivo,
    [Parameter(Mandatory=$true)][string]$Motor,
    [Parameter(Mandatory=$true)][string]$Saida,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$Motor = (Resolve-Path -LiteralPath $Motor).Path
$Arquivo = (Resolve-Path -LiteralPath $Arquivo).Path
$Saida = [IO.Path]::GetFullPath($Saida)
New-Item -ItemType Directory -Path $Saida -Force | Out-Null
Push-Location -LiteralPath $Motor
try {
    & $Python -m motor diario-b3 --arquivo $Arquivo --saida $Saida
    if ($LASTEXITCODE -ne 0) { throw 'Diario bloqueado: confira as mensagens do motor e o CSV.' }
    @{estado='atualizado';gerado_em=(Get-Date).ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Saida 'atualizacao.json') -Encoding UTF8
} catch {
    foreach ($nome in @('diario.json','diario.html')) {
        $p = Join-Path $Saida $nome
        if (Test-Path -LiteralPath $p) { Move-Item -LiteralPath $p -Destination ($p+'.anterior') -Force }
    }
    @{estado='bloqueado';gerado_em=(Get-Date).ToString('o');motivo='Confira o CSV e a saida do motor.'} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Saida 'atualizacao.json') -Encoding UTF8
    throw
} finally { Pop-Location }
