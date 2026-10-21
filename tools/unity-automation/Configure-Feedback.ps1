#requires -Version 5.1
[CmdletBinding()]
param([switch]$EnablePublishing,[switch]$EnableRepairDispatch,
    [string]$StateDirectory=(Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'))
$ErrorActionPreference='Stop'
if ($EnableRepairDispatch) { throw 'API repair dispatch is disabled. Use -EnablePublishing alone for the Codex subscription workflow.' }
if (-not $EnablePublishing) { throw 'Review setup, then explicitly pass -EnablePublishing. No task will be enabled.' }
$path=Join-Path $StateDirectory 'config.json'
if (-not (Test-Path $path)) { throw 'Install/review the validation runner before configuring feedback.' }
$AutomationState=$StateDirectory
. (Join-Path $PSScriptRoot 'Common.ps1')
$gh=(Get-Command gh -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$r=Invoke-AutomationProcess $gh @('auth','status','--hostname','github.com') -Stage 'check GitHub authentication'
if ($r.ExitCode -ne 0) { throw 'Run gh auth login once as the same Windows user, then retry. Do not put tokens in config.json.' }
$r=Invoke-AutomationProcess $gh @('release','view','sunward-unity-feedback','--repo','pep-101-png/okami-minigame') -Stage 'check feedback release'
if ($r.ExitCode -ne 0) {
    $r=Invoke-AutomationProcess $gh @('release','create','sunward-unity-feedback','--repo','pep-101-png/okami-minigame','--target','sunward-minigame','--prerelease','--title','Sunward local Unity feedback','--notes','Automated diagnostic feedback. Generated images/videos require inspection; this release does not approve visual quality.') -Stage 'create reporting prerelease'
    if ($r.ExitCode -ne 0) { throw 'Cannot create reporting release. Check repository contents-write permission.' }
}
$config=Get-Content $path -Raw | ConvertFrom-Json
$config.PublishReports=$true
$config | Add-Member -NotePropertyName DispatchRepair -NotePropertyValue $false -Force
$config | ConvertTo-Json -Depth 10 | Set-Content $path -Encoding UTF8
Write-Host 'Publishing configured for Codex subscription review. No API repair dispatch, task start or task enablement.'
