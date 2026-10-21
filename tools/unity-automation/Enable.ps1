#requires -Version 5.1
param([switch]$StartNow)
$ErrorActionPreference='Stop'
$state=Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
if (-not (Test-Path (Join-Path $state 'config.json'))) { throw 'Install and review config first.' }
Remove-Item (Join-Path $state 'DISABLED') -ErrorAction SilentlyContinue
Enable-ScheduledTask -TaskName SunwardUnityValidation | Out-Null
if ($StartNow) { Start-ScheduledTask -TaskName SunwardUnityValidation }
Write-Host 'Validation enabled at sign-in. Only -StartNow starts it immediately. SunwardGitSync is untouched.'
