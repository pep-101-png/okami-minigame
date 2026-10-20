#requires -Version 5.1
param([string]$Repository = 'C:\Users\giuse\Documents\okami-minigame')
# Resolve the native executable, never a function or alias named Git.
$GitExecutable = (Get-Command -Name git -CommandType Application -ErrorAction Stop |
    Select-Object -First 1).Source
$state = Join-Path $env:LOCALAPPDATA 'SunwardGitSync'
$task = Get-ScheduledTask -TaskName SunwardGitSync -ErrorAction SilentlyContinue
if ($task) {
    $task | Select-Object TaskName,State
    Get-ScheduledTaskInfo -TaskName SunwardGitSync | Select-Object LastRunTime,LastTaskResult
} else { Write-Host 'SunwardGitSync is not installed.' }
& $GitExecutable -C $Repository branch --show-current
& $GitExecutable -C $Repository status --short --branch
if (Test-Path "$state\PAUSED.txt") { Write-Host 'PAUSED:'; Get-Content "$state\PAUSED.txt" }
if (Test-Path "$state\sync.log") { Get-Content "$state\sync.log" -Tail 20 }
