#requires -Version 5.1
$ErrorActionPreference = 'Stop'
Disable-ScheduledTask -TaskName SunwardGitSync | Out-Null
Write-Host 'Future launches disabled. The running task will exit after its current safe cycle.'
$state = Join-Path $env:LOCALAPPDATA 'SunwardGitSync'
New-Item -ItemType Directory -Force -Path $state | Out-Null
'Stopped by user. Review Git status before removing this pause file.' | Set-Content "$state\PAUSED.txt"
# Deliberately do not kill Git in the middle of an index write, commit or transfer.
