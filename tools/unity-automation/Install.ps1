#requires -Version 5.1
param([string]$Repository='C:\Users\giuse\Documents\okami-minigame')
$ErrorActionPreference='Stop'
$Repository=(Resolve-Path $Repository).Path
$state=Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
if (Get-ScheduledTask -TaskName SunwardUnityValidation -ErrorAction SilentlyContinue) { throw 'Task exists. Disable it and wait for exit before explicitly unregistering/reinstalling.' }
New-Item -ItemType Directory -Path $state -Force | Out-Null
foreach ($name in @('Run.ps1','Common.ps1','Video.ps1')) { Copy-Item (Join-Path $PSScriptRoot $name) (Join-Path $state $name) }
if (-not (Test-Path (Join-Path $state 'config.json'))) { Copy-Item (Join-Path $PSScriptRoot 'config.example.json') (Join-Path $state 'config.json') }
'Installed disabled. Review config and run a manual smoke test before enabling.' | Set-Content (Join-Path $state 'DISABLED')
$executable=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments='-NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "{0}" -Repository "{1}" -Watch' -f (Join-Path $state 'Run.ps1'),$Repository
$action=New-ScheduledTaskAction -Execute $executable -Argument $arguments -WorkingDirectory $state
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$task=New-ScheduledTask -Action $action -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $user) -Principal (New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited) -Settings (New-ScheduledTaskSettingsSet -Disable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)
Register-ScheduledTask -TaskName SunwardUnityValidation -InputObject $task | Out-Null
Write-Host 'Installed DISABLED; existing SunwardGitSync task is untouched. No Unity/validation task was started.'
