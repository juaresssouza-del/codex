param(
    [Parameter(Mandatory=$true)][string]$Arquivo,
    [Parameter(Mandatory=$true)][string]$Motor,
    [Parameter(Mandatory=$true)][string]$Saida,
    [string]$Python = 'python',
    [ValidateSet('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')]
    [string]$Dia = 'Sunday',
    [string]$Hora = '19:00',
    [string]$Nome = 'TradeLab-Diario-Simulador'
)
$ErrorActionPreference = 'Stop'
$scriptAtualizar = Join-Path $PSScriptRoot 'Atualizar-Diario.ps1'
$Motor = (Resolve-Path -LiteralPath $Motor).Path
$Arquivo = (Resolve-Path -LiteralPath $Arquivo).Path
$Saida = [IO.Path]::GetFullPath($Saida)
$Python = (Get-Command $Python -ErrorAction Stop).Source
foreach ($p in @($scriptAtualizar,$Motor,$Arquivo,$Saida,$Python)) {
    if ($p.Contains('"')) { throw 'Caminho com aspas nao suportado.' }
}
if (Get-ScheduledTask -TaskName $Nome -ErrorAction SilentlyContinue) {
    throw 'Ja existe uma tarefa com esse nome. Revise a tarefa existente ou escolha outro Nome.'
}
$argsTarefa = '-NoProfile -NonInteractive -File "{0}" -Arquivo "{1}" -Motor "{2}" -Saida "{3}" -Python "{4}"' -f $scriptAtualizar,$Arquivo,$Motor,$Saida,$Python
$acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argsTarefa
$gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Dia -At ([datetime]::ParseExact($Hora,'HH:mm',[Globalization.CultureInfo]::InvariantCulture))
$usuario = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Limited
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $Nome -Action $acao -Trigger $gatilho -Principal $principal -Settings $config | Out-Null
Write-Output ('Tarefa instalada para {0} as {1}, fuso do Windows: {2}. Requer usuario conectado.' -f $Dia,$Hora,(Get-TimeZone).Id)
