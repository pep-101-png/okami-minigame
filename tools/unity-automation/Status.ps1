#requires -Version 5.1
$state=Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
$task=Get-ScheduledTask -TaskName SunwardUnityValidation -ErrorAction SilentlyContinue
if ($task) { $task | Select-Object TaskName,State; Get-ScheduledTaskInfo -TaskName SunwardUnityValidation | Select-Object LastRunTime,LastTaskResult }
else { Write-Host 'Validation task not installed.' }
Write-Host "Disabled marker: $(Test-Path (Join-Path $state 'DISABLED'))"
if (Test-Path (Join-Path $state 'last-run.json')) { Get-Content (Join-Path $state 'last-run.json') }
if (Test-Path (Join-Path $state 'runner.log')) { Get-Content (Join-Path $state 'runner.log') -Tail 15 }
