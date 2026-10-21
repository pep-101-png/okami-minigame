#requires -Version 5.1
$ErrorActionPreference='Stop'
$state=Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
New-Item -ItemType Directory -Path $state -Force | Out-Null
'Operator disabled validation.' | Set-Content (Join-Path $state 'DISABLED')
$task=Get-ScheduledTask -TaskName SunwardUnityValidation -ErrorAction SilentlyContinue
if ($task) { Disable-ScheduledTask -TaskName SunwardUnityValidation | Out-Null }
Write-Host 'Validation disabled. An owned Unity process is cancelled at the next watchdog check. No user editor or sync task is stopped.'
