#requires -Version 5.1
param([string]$Repository = 'C:\Users\giuse\Documents\okami-minigame')
$state = Join-Path $env:LOCALAPPDATA 'SunwardGitSync'
$task = Get-ScheduledTask -TaskName SunwardGitSync -ErrorAction SilentlyContinue
if ($task) {
    $task | Select-Object TaskName,State
    Get-ScheduledTaskInfo -TaskName SunwardGitSync | Select-Object LastRunTime,LastTaskResult
} else { Write-Host 'SunwardGitSync is not installed.' }
& git -C $Repository branch --show-current
& git -C $Repository status --short --branch
if (Test-Path "$state\PAUSED.txt") { Write-Host 'PAUSED:'; Get-Content "$state\PAUSED.txt" }
if (Test-Path "$state\sync.log") { Get-Content "$state\sync.log" -Tail 20 }
