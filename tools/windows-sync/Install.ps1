#requires -Version 5.1
[CmdletBinding()]
param([string]$Repository = 'C:\Users\giuse\Documents\okami-minigame')
$ErrorActionPreference = 'Stop'
# Resolve the native executable, never a function or alias named Git.
$GitExecutable = (Get-Command -Name git -CommandType Application -ErrorAction Stop |
    Select-Object -First 1).Source
$Repository = (Resolve-Path -LiteralPath $Repository).Path
if ((& $GitExecutable -C $Repository branch --show-current) -cne 'sunward-minigame') {
    throw 'Switch to sunward-minigame manually after reviewing local work. Installer never switches branches.'
}
& $GitExecutable -C $Repository lfs install --local
if ($LASTEXITCODE -ne 0) { throw 'Git LFS setup failed. Review existing hooks; do not force-install.' }
$state = Join-Path $env:LOCALAPPDATA 'SunwardGitSync'
New-Item -ItemType Directory -Force -Path $state | Out-Null
$script = Join-Path $state 'Sync.ps1'
$taskName = 'SunwardGitSync'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task already exists. Stop and unregister it explicitly before reinstalling.'
}
# Run the reviewed copy, so a remote script update cannot change the running service.
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Sync.ps1') -Destination $script
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$taskArguments = '-NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "{0}" -Repository "{1}" -Apply -Watch' -f $script,$Repository
$action = New-ScheduledTaskAction -Execute $exe -Argument $taskArguments -WorkingDirectory $Repository
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Disable
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Register-ScheduledTask -TaskName $taskName -InputObject $task | Out-Null
Write-Host 'Installed DISABLED. No sync was started. Read README.md before enabling.'
